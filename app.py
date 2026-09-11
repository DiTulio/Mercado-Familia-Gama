from flask import Flask, request, jsonify, session, g
import sqlite3
import hashlib
import hmac
import os
import json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gama-dev-secret-2025")  # Troque em produção!
DATABASE = "mercado_gama.db"

def get_db():
    """Retorna conexão com o banco para o contexto atual da requisição."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row   # resultados como dicionários
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    """Cria todas as tabelas se ainda não existirem."""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA_SQL)
    db.commit()
    db.close()
    print("✅ Banco de dados inicializado.")

SCHEMA_SQL = """
-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    senha_hash    TEXT    NOT NULL,
    telefone      TEXT,
    endereco      TEXT,
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    ultimo_login  TEXT
);

-- Tabela de Produtos
CREATE TABLE IF NOT EXISTS produtos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    marca         TEXT,
    categoria     TEXT    NOT NULL,
    preco         REAL    NOT NULL CHECK(preco >= 0),
    unidade       TEXT    NOT NULL DEFAULT '/un',
    emoji         TEXT    DEFAULT '🛒',
    estoque       INTEGER NOT NULL DEFAULT 0,
    ativo         INTEGER NOT NULL DEFAULT 1,  -- 1=ativo, 0=inativo
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Tabela de Pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
    status        TEXT    NOT NULL DEFAULT 'pendente',
    -- Status possíveis: pendente | confirmado | em_preparo | saiu_entrega | entregue | cancelado
    endereco_entrega TEXT NOT NULL,
    distancia_km  REAL,
    frete         REAL    NOT NULL DEFAULT 0,
    subtotal      REAL    NOT NULL DEFAULT 0,
    total         REAL    NOT NULL DEFAULT 0,
    observacao    TEXT,
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    atualizado_em TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Itens de cada Pedido
CREATE TABLE IF NOT EXISTS itens_pedido (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id     INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id    INTEGER NOT NULL REFERENCES produtos(id),
    nome_produto  TEXT    NOT NULL,   -- cópia do nome no momento da compra
    preco_unitario REAL   NOT NULL,   -- cópia do preço no momento da compra
    quantidade    INTEGER NOT NULL CHECK(quantidade > 0),
    subtotal      REAL    NOT NULL
);

-- Histórico de visualizações (base para recomendações)
CREATE TABLE IF NOT EXISTS historico_visualizacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
    produto_id    INTEGER NOT NULL REFERENCES produtos(id),
    visto_em      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Notificações (promoções, novidades, novas unidades)
CREATE TABLE IF NOT EXISTS notificacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo        TEXT    NOT NULL,
    mensagem      TEXT    NOT NULL,
    tipo          TEXT    NOT NULL DEFAULT 'geral',
    -- tipos: geral | promocao | novidade | nova_unidade
    produto_id    INTEGER REFERENCES produtos(id),  -- opcional: produto relacionado
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    ativo         INTEGER NOT NULL DEFAULT 1
);

-- Relacionamento: quais notificações o usuário já leu
CREATE TABLE IF NOT EXISTS notificacoes_lidas (
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
    notificacao_id INTEGER NOT NULL REFERENCES notificacoes(id),
    lido_em       TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    PRIMARY KEY (usuario_id, notificacao_id)
);
"""

def hash_senha(senha: str) -> str:
    """Gera hash seguro da senha usando PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, 260_000)
    return salt.hex() + ":" + dk.hex()

def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha confere com o hash armazenado."""
    try:
        salt_hex, dk_hex = senha_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        dk   = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, 260_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False

def login_necessario(f):
    """Decorator: bloqueia a rota se o usuário não estiver logado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"erro": "Login necessário"}), 401
        return f(*args, **kwargs)
    return decorated

def usuario_logado():
    uid = session.get("usuario_id")
    if not uid:
        return None
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone()
    return dict(row) if row else None

def gerar_recomendacoes(usuario_id: int, limite: int = 5) -> list:
    """
    Recomenda produtos baseado nas categorias que o usuário
    mais comprou. Estratégia simples e eficiente para MVP.
    """
    db = get_db()

    # Categorias mais compradas pelo usuário
    categorias = db.execute("""
        SELECT p.categoria, COUNT(*) as qtd
        FROM itens_pedido ip
        JOIN produtos p ON p.id = ip.produto_id
        JOIN pedidos   pe ON pe.id = ip.pedido_id
        WHERE pe.usuario_id = ?
        GROUP BY p.categoria
        ORDER BY qtd DESC
        LIMIT 3
    """, (usuario_id,)).fetchall()

    if not categorias:
        # Usuário sem histórico: retorna os mais vendidos geral
        rows = db.execute("""
            SELECT p.*, SUM(ip.quantidade) as vendas
            FROM produtos p
            JOIN itens_pedido ip ON ip.produto_id = p.id
            WHERE p.ativo = 1
            GROUP BY p.id
            ORDER BY vendas DESC
            LIMIT ?
        """, (limite,)).fetchall()
        return [dict(r) for r in rows]

    cats = [r["categoria"] for r in categorias]
    placeholders = ",".join("?" * len(cats))

    # Produtos dessas categorias que o usuário ainda não comprou
    rows = db.execute(f"""
        SELECT p.*
        FROM produtos p
        WHERE p.ativo = 1
        AND p.categoria IN ({placeholders})
        AND p.id NOT IN (
            SELECT DISTINCT ip.produto_id
            FROM itens_pedido ip
            JOIN pedidos pe ON pe.id = ip.pedido_id
            WHERE pe.usuario_id = ?
        )
        ORDER BY RANDOM()
        LIMIT ?
    """, (*cats, usuario_id, limite)).fetchall()

    return [dict(r) for r in rows]

# ──────────────────────────────────────────────
#  ROTAS — Autenticação
# ──────────────────────────────────────────────

@app.route("/api/cadastro", methods=["POST"])
def cadastro():
    """Cria uma nova conta de usuário."""
    data = request.get_json(silent=True) or {}
    nome     = (data.get("nome") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    senha    = data.get("senha") or ""
    telefone = (data.get("telefone") or "").strip()
    endereco = (data.get("endereco") or "").strip()

    # Validações básicas
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, e-mail e senha são obrigatórios."}), 400
    if len(senha) < 6:
        return jsonify({"erro": "A senha deve ter pelo menos 6 caracteres."}), 400

    db = get_db()
    if db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone():
        return jsonify({"erro": "E-mail já cadastrado."}), 409

    db.execute("""
        INSERT INTO usuarios (nome, email, senha_hash, telefone, endereco)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, email, hash_senha(senha), telefone, endereco))
    db.commit()

    usuario = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    session["usuario_id"] = usuario["id"]

    return jsonify({
        "mensagem": f"Bem-vindo(a) ao Mercado Família Gama, {nome}!",
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"]
        }
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    """Autentica o usuário e inicia sessão."""
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""

    if not email or not senha:
        return jsonify({"erro": "E-mail e senha são obrigatórios."}), 400

    db = get_db()
    usuario = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    if not usuario or not verificar_senha(senha, usuario["senha_hash"]):
        return jsonify({"erro": "E-mail ou senha incorretos."}), 401

    # Atualiza último login
    db.execute("UPDATE usuarios SET ultimo_login = datetime('now','localtime') WHERE id = ?",
            (usuario["id"],))
    db.commit()
    session["usuario_id"] = usuario["id"]

    return jsonify({
        "mensagem": f"Bem-vindo(a) de volta, {usuario['nome']}!",
        "usuario": {
            "id":    usuario["id"],
            "nome":  usuario["nome"],
            "email": usuario["email"]
        }
    })


@app.route("/api/logout", methods=["POST"])
@login_necessario
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    return jsonify({"mensagem": "Você saiu com sucesso."})


@app.route("/api/perfil", methods=["GET"])
@login_necessario
def perfil():
    """Retorna os dados do perfil do usuário logado."""
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    db = get_db()

    # Total de pedidos e valor gasto
    stats = db.execute("""
        SELECT COUNT(*) as total_pedidos, COALESCE(SUM(total), 0) as total_gasto
        FROM pedidos WHERE usuario_id = ? AND status != 'cancelado'
    """, (usuario["id"],)).fetchone()

    # Último pedido
    ultimo = db.execute("""
        SELECT id, status, total, criado_em FROM pedidos
        WHERE usuario_id = ? ORDER BY criado_em DESC LIMIT 1
    """, (usuario["id"],)).fetchone()

    return jsonify({
        "usuario": {
            "id":           usuario["id"],
            "nome":         usuario["nome"],
            "email":        usuario["email"],
            "telefone":     usuario["telefone"],
            "endereco":     usuario["endereco"],
            "criado_em":    usuario["criado_em"],
            "ultimo_login": usuario["ultimo_login"],
        },
        "estatisticas": {
            "total_pedidos": stats["total_pedidos"],
            "total_gasto":   round(stats["total_gasto"], 2),
        },
        "ultimo_pedido": dict(ultimo) if ultimo else None
    })


@app.route("/api/perfil", methods=["PUT"])
@login_necessario
def atualizar_perfil():
    """Atualiza nome, telefone e endereço do usuário."""
    data     = request.get_json(silent=True) or {}
    usuario  = usuario_logado()
    db       = get_db()

    campos   = {}
    if "nome" in data and data["nome"].strip():
        campos["nome"] = data["nome"].strip()
    if "telefone" in data:
        campos["telefone"] = data["telefone"].strip()
    if "endereco" in data:
        campos["endereco"] = data["endereco"].strip()

    if not campos:
        return jsonify({"erro": "Nenhum campo para atualizar."}), 400

    set_clause = ", ".join(f"{k} = ?" for k in campos)
    db.execute(
        f"UPDATE usuarios SET {set_clause} WHERE id = ?",
        (*campos.values(), usuario["id"])
    )
    db.commit()
    return jsonify({"mensagem": "Perfil atualizado com sucesso!"})

# ──────────────────────────────────────────────
#  ROTAS — Produtos
# ──────────────────────────────────────────────

@app.route("/api/produtos", methods=["GET"])
def listar_produtos():
    """Lista produtos com filtro opcional por categoria."""
    categoria = request.args.get("categoria")
    busca     = request.args.get("busca", "").strip()
    db        = get_db()

    query  = "SELECT * FROM produtos WHERE ativo = 1"
    params = []

    if categoria:
        query  += " AND categoria = ?"
        params.append(categoria)
    if busca:
        query  += " AND (nome LIKE ? OR marca LIKE ?)"
        params += [f"%{busca}%", f"%{busca}%"]

    query += " ORDER BY categoria, nome"
    rows  = db.execute(query, params).fetchall()

    return jsonify([dict(r) for r in rows])


@app.route("/api/produtos/<int:pid>", methods=["GET"])
def detalhe_produto(pid):
    """Retorna detalhes de um produto específico."""
    row = get_db().execute("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (pid,)).fetchone()
    if not row:
        return jsonify({"erro": "Produto não encontrado."}), 404
    return jsonify(dict(row))


@app.route("/api/recomendacoes", methods=["GET"])
@login_necessario
def recomendacoes():
    """Retorna produtos recomendados para o usuário logado."""
    usuario = usuario_logado()
    limite  = int(request.args.get("limite", 6))
    prods   = gerar_recomendacoes(usuario["id"], limite)
    return jsonify({
        "recomendacoes": prods,
        "total": len(prods)
    })

# ──────────────────────────────────────────────
#  ROTAS — Pedidos
# ──────────────────────────────────────────────

@app.route("/api/pedidos", methods=["POST"])
@login_necessario
def criar_pedido():
    """
    Cria um novo pedido.
    Body esperado:
    {
        "endereco_entrega": "Rua X, 123 - São Paulo",
        "distancia_km": 4.5,
        "frete": 2.50,
        "itens": [
            {"produto_id": 1, "quantidade": 2},
            {"produto_id": 5, "quantidade": 1}
        ],
        "observacao": "Sem campainha, ligar ao chegar"
    }
    """
    data    = request.get_json(silent=True) or {}
    usuario = usuario_logado()
    db      = get_db()

    endereco = (data.get("endereco_entrega") or "").strip()
    itens    = data.get("itens") or []

    if not endereco:
        return jsonify({"erro": "Endereço de entrega é obrigatório."}), 400
    if not itens:
        return jsonify({"erro": "O pedido precisa ter ao menos um item."}), 400

    distancia = data.get("distancia_km", 0)
    frete     = data.get("frete", 0)
    observacao = data.get("observacao", "")

    # Valida e calcula subtotal
    subtotal = 0.0
    itens_validados = []

    for item in itens:
        pid = item.get("produto_id")
        qty = item.get("quantidade", 1)

        if not pid or qty < 1:
            return jsonify({"erro": f"Item inválido: {item}"}), 400

        produto = db.execute(
            "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (pid,)
        ).fetchone()

        if not produto:
            return jsonify({"erro": f"Produto ID {pid} não encontrado ou inativo."}), 404

        sub = round(produto["preco"] * qty, 2)
        subtotal += sub
        itens_validados.append({
            "produto_id":    pid,
            "nome_produto":  produto["nome"],
            "preco_unitario": produto["preco"],
            "quantidade":    qty,
            "subtotal":      sub
        })

    subtotal = round(subtotal, 2)
    total    = round(subtotal + frete, 2)

    # Insere o pedido
    cur = db.execute("""
        INSERT INTO pedidos
            (usuario_id, endereco_entrega, distancia_km, frete, subtotal, total, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (usuario["id"], endereco, distancia, frete, subtotal, total, observacao))

    pedido_id = cur.lastrowid

    # Insere os itens
    for item in itens_validados:
        db.execute("""
            INSERT INTO itens_pedido
                (pedido_id, produto_id, nome_produto, preco_unitario, quantidade, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pedido_id, item["produto_id"], item["nome_produto"],
            item["preco_unitario"], item["quantidade"], item["subtotal"]))

    db.commit()

    return jsonify({
        "mensagem": "Pedido realizado com sucesso! 🎉",
        "pedido": {
            "id":       pedido_id,
            "status":   "pendente",
            "subtotal": subtotal,
            "frete":    frete,
            "total":    total
        }
    }), 201


@app.route("/api/pedidos", methods=["GET"])
@login_necessario
def listar_pedidos():
    """Lista todos os pedidos do usuário logado."""
    usuario = usuario_logado()
    db      = get_db()

    pedidos = db.execute("""
        SELECT * FROM pedidos
        WHERE usuario_id = ?
        ORDER BY criado_em DESC
    """, (usuario["id"],)).fetchall()

    resultado = []
    for p in pedidos:
        itens = db.execute("""
            SELECT * FROM itens_pedido WHERE pedido_id = ?
        """, (p["id"],)).fetchall()

        resultado.append({
            **dict(p),
            "itens": [dict(i) for i in itens]
        })

    return jsonify(resultado)


@app.route("/api/pedidos/<int:pid>", methods=["GET"])
@login_necessario
def detalhe_pedido(pid):
    """Retorna detalhes de um pedido específico do usuário."""
    usuario = usuario_logado()
    db      = get_db()

    pedido = db.execute(
        "SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?",
        (pid, usuario["id"])
    ).fetchone()

    if not pedido:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    itens = db.execute(
        "SELECT * FROM itens_pedido WHERE pedido_id = ?", (pid,)
    ).fetchall()

    return jsonify({
        **dict(pedido),
        "itens": [dict(i) for i in itens]
    })

# ──────────────────────────────────────────────
#  ROTAS — Notificações
# ──────────────────────────────────────────────

@app.route("/api/notificacoes", methods=["GET"])
@login_necessario
def notificacoes():
    """Retorna as notificações não lidas do usuário."""
    usuario = usuario_logado()
    db      = get_db()

    rows = db.execute("""
        SELECT n.*,
            CASE WHEN nl.usuario_id IS NOT NULL THEN 1 ELSE 0 END AS lida
        FROM notificacoes n
        LEFT JOIN notificacoes_lidas nl
            ON nl.notificacao_id = n.id AND nl.usuario_id = ?
        WHERE n.ativo = 1
        ORDER BY n.criado_em DESC
        LIMIT 20
    """, (usuario["id"],)).fetchall()

    nao_lidas = sum(1 for r in rows if not r["lida"])

    return jsonify({
        "notificacoes": [dict(r) for r in rows],
        "nao_lidas":    nao_lidas
    })


@app.route("/api/notificacoes/<int:nid>/ler", methods=["POST"])
@login_necessario
def marcar_lida(nid):
    """Marca uma notificação como lida."""
    usuario = usuario_logado()
    db      = get_db()
    db.execute("""
        INSERT OR IGNORE INTO notificacoes_lidas (usuario_id, notificacao_id)
        VALUES (?, ?)
    """, (usuario["id"], nid))
    db.commit()
    return jsonify({"mensagem": "Notificação marcada como lida."})


# ──────────────────────────────────────────────
#  SEED — importa e roda dados de demonstração
# ──────────────────────────────────────────────
def seed_demo():
    """Popula o banco com dados de exemplo na primeira execução."""
    import os
    # Só roda seed se o banco foi criado agora (produtos vazio)
    db = sqlite3.connect(DATABASE)
    count = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    db.close()
    if count == 0:
        from seed import seed
        seed(DATABASE)
    else:
        print(f"ℹ️  Banco já populado ({count} produtos). Seed ignorado.")

# ──────────────────────────────────────────────
#  ROTA RAIZ — painel de teste simples
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <title>Mercado Família Gama — API</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0033A0; color: #fff;
            display: flex; align-items: center; justify-content: center;
            min-height: 100vh; margin: 0; }
        .box { background: #fff; color: #1a1a2e; border-radius: 18px;
            padding: 40px 50px; max-width: 560px; width: 90%;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
        h1   { color: #0033A0; font-size: 1.8rem; margin-bottom: 6px; }
        h1 span { color: #D01010; }
        p    { color: #555; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
        th   { background: #0033A0; color: #fff; padding: 8px 12px; text-align: left; }
        td   { padding: 8px 12px; border-bottom: 1px solid #e0e3ed; }
        tr:last-child td { border-bottom: none; }
        .m   { background: #e3f2fd; color: #0033A0; border-radius: 4px;
            padding: 2px 6px; font-weight: 700; font-size: 0.78rem; }
        .post { background: #fff8e1; color: #e65100; }
        .put  { background: #f3e5f5; color: #6a1b9a; }
        .del  { background: #ffebee; color: #b71c1c; }
    </style>
    </head>
    <body>
    <div class="box">
    <h1>🛒 Mercado <span>Família Gama</span></h1>
    <p>Back-end Python funcionando! Endpoints disponíveis:</p>
    <table>
        <tr><th>Método</th><th>Rota</th><th>Descrição</th></tr>
        <tr><td><span class="m post">POST</span></td><td>/api/cadastro</td><td>Criar conta</td></tr>
        <tr><td><span class="m post">POST</span></td><td>/api/login</td><td>Fazer login</td></tr>
        <tr><td><span class="m post">POST</span></td><td>/api/logout</td><td>Sair</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/perfil</td><td>Ver perfil</td></tr>
        <tr><td><span class="m put">PUT</span></td><td>/api/perfil</td><td>Editar perfil</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/produtos</td><td>Listar produtos</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/produtos/&lt;id&gt;</td><td>Detalhe produto</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/recomendacoes</td><td>Recomendações</td></tr>
        <tr><td><span class="m post">POST</span></td><td>/api/pedidos</td><td>Criar pedido</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/pedidos</td><td>Meus pedidos</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/pedidos/&lt;id&gt;</td><td>Detalhe pedido</td></tr>
        <tr><td><span class="m">GET</span></td><td>/api/notificacoes</td><td>Notificações</td></tr>
        <tr><td><span class="m post">POST</span></td><td>/api/notificacoes/&lt;id&gt;/ler</td><td>Marcar lida</td></tr>
    </table>
    </div>
    </body>
    </html>
    """

# ──────────────────────────────────────────────
#  INICIALIZAÇÃO
# ──────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    seed_demo()          # Popula com dados de exemplo
    print("\n🚀 Servidor rodando em http://localhost:5000\n")
    app.run(debug=True, port=5000)