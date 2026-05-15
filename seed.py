"""
seed.py — Popula o banco com dados de demonstração.
Execute: python seed.py
(O app.py já chama seed_demo() automaticamente na primeira vez.)
"""

import sqlite3
import hashlib
import hmac
import os

DATABASE = "mercado_gama.db"


def hash_senha(senha: str) -> str:
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, 260_000)
    return salt.hex() + ":" + dk.hex()


def seed(db_path=DATABASE):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")

    # ── Produtos ───────────────────────────────────────────────
    produtos = [
        # (nome, marca, categoria, preco, unidade, emoji, estoque)
        ("Picanha Bovina",        "Corte Nobre",      "acougue",    79.90, "/kg",      "🥩", 50),
        ("Alcatra Bovina",        "Friboi",            "acougue",    49.90, "/kg",      "🥩", 60),
        ("Frango Inteiro",        "Seara",             "acougue",    12.90, "/kg",      "🍗", 80),
        ("Frango Inteiro",        "Sadia",             "acougue",    11.90, "/kg",      "🍗", 80),
        ("Costela Suína",         "Rezende",           "acougue",    24.90, "/kg",      "🥓", 40),
        ("Linguiça Calabresa",    "Seara",             "acougue",    18.90, "/kg",      "🌭", 70),
        ("Linguiça Calabresa",    "Rezende",           "acougue",    17.50, "/kg",      "🌭", 70),
        ("Filé de Tilápia",       "Bom Peixe",         "acougue",    29.90, "/kg",      "🐟", 30),
        ("Tomate Italiano",       "Campo Verde",       "hortifruti",  5.90, "/kg",      "🍅", 100),
        ("Tomate Cereja",         "Horta Natural",     "hortifruti",  7.90, "/bandeja", "🍅", 60),
        ("Brócolis",              "Vida Verde",        "hortifruti",  4.50, "/un",      "🥦", 50),
        ("Banana Prata",          "Fazenda Boa Vista", "hortifruti",  3.99, "/kg",      "🍌", 120),
        ("Banana Nanica",         "Sítio Gama",        "hortifruti",  3.49, "/kg",      "🍌", 120),
        ("Laranja Pêra",          "Citrus SP",         "hortifruti",  4.90, "/kg",      "🍊", 90),
        ("Maçã Fuji",             "Fruticultura Sul",  "hortifruti",  8.90, "/kg",      "🍎", 70),
        ("Batata Inglesa",        "Campo Vivo",        "hortifruti",  3.99, "/kg",      "🥔", 110),
        ("Leite Integral 1L",     "Italac",            "laticinios",  5.49, "/un",      "🥛", 200),
        ("Leite Integral 1L",     "Parmalat",          "laticinios",  5.99, "/un",      "🥛", 200),
        ("Queijo Mussarela",      "Tirolez",           "laticinios", 42.90, "/kg",      "🧀", 40),
        ("Queijo Mussarela",      "Quatá",             "laticinios", 39.90, "/kg",      "🧀", 40),
        ("Iogurte Natural 170g",  "Danone",            "laticinios",  3.99, "/un",      "🫙", 150),
        ("Iogurte Natural 170g",  "Nestlé",            "laticinios",  3.49, "/un",      "🫙", 150),
        ("Manteiga 200g",         "Aviação",           "laticinios",  9.90, "/un",      "🧈", 80),
        ("Manteiga 200g",         "Batavo",            "laticinios", 11.50, "/un",      "🧈", 80),
        ("Pão Francês",           "Padaria Gama",      "padaria",     0.79, "/un",      "🍞", 300),
        ("Pão de Forma 500g",     "Wickbold",          "padaria",     7.90, "/un",      "🍞", 60),
        ("Pão de Forma 500g",     "Pullman",           "padaria",     6.99, "/un",      "🍞", 60),
        ("Croissant",             "Padaria Gama",      "padaria",     3.50, "/un",      "🥐", 50),
        ("Bolo de Cenoura",       "Padaria Gama",      "padaria",    18.90, "/un",      "🎂", 20),
        ("Pão de Queijo",         "Forno de Minas",    "padaria",     1.50, "/un",      "🥨", 100),
        ("Refrigerante 2L",       "Coca-Cola",         "bebidas",     9.90, "/un",      "🥤", 150),
        ("Refrigerante 2L",       "Pepsi",             "bebidas",     8.90, "/un",      "🥤", 120),
        ("Refrigerante 2L",       "Guaraná Antarctica","bebidas",     6.49, "/un",      "🥤", 130),
        ("Cerveja Lata 350ml",    "Brahma",            "bebidas",     4.50, "/un",      "🍺", 200),
        ("Cerveja Lata 350ml",    "Heineken",          "bebidas",     4.99, "/un",      "🍺", 180),
        ("Suco de Uva 1L",        "Welch's",           "bebidas",    12.90, "/un",      "🧃", 60),
        ("Suco de Laranja 1L",    "Del Valle",         "bebidas",    10.90, "/un",      "🧃", 70),
        ("Água Mineral 500ml",    "Crystal",           "bebidas",     2.50, "/un",      "💧", 300),
        ("Água Mineral 500ml",    "Bonafont",          "bebidas",     2.29, "/un",      "💧", 300),
        ("Detergente 500ml",      "Ypê",               "limpeza",     2.99, "/un",      "🧴", 120),
        ("Detergente 500ml",      "Limpol",            "limpeza",     3.49, "/un",      "🧴", 100),
        ("Sabão em Pó 1kg",       "Omo",               "limpeza",    14.90, "/un",      "🫧", 80),
        ("Sabão em Pó 1kg",       "Ariel",             "limpeza",    11.90, "/un",      "🫧", 80),
        ("Amaciante 2L",          "Downy",             "limpeza",    12.90, "/un",      "🫙", 60),
        ("Amaciante 2L",          "Comfort",           "limpeza",    10.50, "/un",      "🫙", 60),
        ("Desinfetante 500ml",    "Pinho Sol",         "limpeza",     4.90, "/un",      "🧹", 90),
        ("Arroz Tipo 1 5kg",      "Camil",             "mercearia",  22.90, "/un",      "🌾", 100),
        ("Arroz Tipo 1 5kg",      "Tio João",          "mercearia",  20.90, "/un",      "🌾", 100),
        ("Feijão Carioca 1kg",    "Camil",             "mercearia",   8.90, "/un",      "🫘", 90),
        ("Feijão Carioca 1kg",    "Kicaldo",           "mercearia",   7.90, "/un",      "🫘", 90),
        ("Óleo de Soja 900ml",    "Soya",              "mercearia",   6.99, "/un",      "🫒", 80),
        ("Macarrão Espaguete 500g","Barilla",           "mercearia",   4.49, "/un",      "🍝", 70),
        ("Macarrão Espaguete 500g","Adria",             "mercearia",   3.29, "/un",      "🍝", 70),
        ("Açúcar Cristal 1kg",    "União",             "mercearia",   4.99, "/un",      "🍬", 100),
        ("Sabonete em Barra",     "Lux",               "higiene",     2.49, "/un",      "🧼", 150),
        ("Sabonete em Barra",     "Dove",              "higiene",     2.99, "/un",      "🧼", 150),
        ("Shampoo 400ml",         "Pantene",           "higiene",    14.90, "/un",      "🧴", 80),
        ("Shampoo 400ml",         "Seda",              "higiene",    13.50, "/un",      "🧴", 80),
        ("Pasta de Dente 90g",    "Colgate",           "higiene",     5.90, "/un",      "🪥", 120),
        ("Pasta de Dente 90g",    "Oral-B",            "higiene",     5.49, "/un",      "🪥", 120),
        ("Papel Higiênico 4 rolos","Neve",             "higiene",     9.90, "/pc",      "🧻", 90),
        ("Papel Higiênico 4 rolos","Personal",         "higiene",     8.90, "/pc",      "🧻", 90),
    ]

    for p in produtos:
        db.execute("""
            INSERT OR IGNORE INTO produtos (nome, marca, categoria, preco, unidade, emoji, estoque)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, p)

    # ── Usuários de demonstração ────────────────────────────────
    usuarios = [
        ("Ana Gama",   "ana@exemplo.com",   "senha123", "(11) 99999-0001", "Rua das Flores, 100 - Taboão da Serra/SP"),
        ("Carlos Lima","carlos@exemplo.com","senha123", "(11) 99999-0002", "Av. Central, 500 - Taboão da Serra/SP"),
    ]

    for u in usuarios:
        existing = db.execute("SELECT id FROM usuarios WHERE email = ?", (u[1],)).fetchone()
        if not existing:
            db.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, telefone, endereco)
                VALUES (?, ?, ?, ?, ?)
            """, (u[0], u[1], hash_senha(u[2]), u[3], u[4]))

    db.commit()

    ana = db.execute("SELECT id FROM usuarios WHERE email = 'ana@exemplo.com'").fetchone()
    if ana:
        uid = ana[0]
        pedido_existente = db.execute("SELECT id FROM pedidos WHERE usuario_id = ?", (uid,)).fetchone()
        if not pedido_existente:
            p1 = db.execute("SELECT id, preco FROM produtos WHERE nome = 'Arroz Tipo 1 5kg' AND marca = 'Camil'").fetchone()
            p2 = db.execute("SELECT id, preco FROM produtos WHERE nome = 'Feijão Carioca 1kg' AND marca = 'Camil'").fetchone()
            p3 = db.execute("SELECT id, preco FROM produtos WHERE nome = 'Leite Integral 1L' AND marca = 'Italac'").fetchone()

            if p1 and p2 and p3:
                subtotal = round(p1[1]*2 + p2[1]*2 + p3[1]*4, 2)
                frete    = 2.50
                total    = round(subtotal + frete, 2)

                cur = db.execute("""
                    INSERT INTO pedidos (usuario_id, status, endereco_entrega, distancia_km, frete, subtotal, total)
                    VALUES (?, 'entregue', 'Rua das Flores, 100 - Taboão da Serra/SP', 4.2, ?, ?, ?)
                """, (uid, frete, subtotal, total))
                pid = cur.lastrowid

                for prod, qty in [(p1, 2), (p2, 2), (p3, 4)]:
                    db.execute("""
                        INSERT INTO itens_pedido (pedido_id, produto_id, nome_produto, preco_unitario, quantidade, subtotal)
                        SELECT ?, id, nome, preco, ?, preco * ?
                        FROM produtos WHERE id = ?
                    """, (pid, qty, qty, prod[0]))

    # ── Notificações de exemplo ─────────────────────────────────
    notifs = [
        ("🎉 Promoção da Semana!",
         "Frango Seara e Sadia com 15% de desconto até domingo. Aproveite!",
         "promocao", 3),
        ("🆕 Novidade no Catálogo",
         "Chegou o Queijo Prato Tirolez e mais novidades na seção de Laticínios!",
         "novidade", 19),
        ("🏪 Nova Unidade em Breve",
         "Em breve abrimos nossa segunda unidade no centro de Taboão da Serra. Fique atento!",
         "nova_unidade", None),
        ("💧 Estoque Renovado",
         "Água mineral Crystal e Bonafont já disponíveis em quantidade. Estoque reforçado!",
         "geral", 38),
    ]

    for titulo, msg, tipo, prod_id in notifs:
        existe = db.execute("SELECT id FROM notificacoes WHERE titulo = ?", (titulo,)).fetchone()
        if not existe:
            db.execute("""
                INSERT INTO notificacoes (titulo, mensagem, tipo, produto_id)
                VALUES (?, ?, ?, ?)
            """, (titulo, msg, tipo, prod_id))

    db.commit()
    db.close()
    print("✅ Dados de demonstração inseridos com sucesso!")
    print("\n📧 Usuários de teste criados:")
    print("   ana@exemplo.com     / senha123")
    print("   carlos@exemplo.com  / senha123")


if __name__ == "__main__":
    seed()