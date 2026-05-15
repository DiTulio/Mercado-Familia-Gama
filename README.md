# 🛒 Mercado Família Gama — Back-end Python

Protótipo do sistema de armazenamento de dados do site.  
**Stack:** Python 3 · Flask · SQLite

---

## 📁 Estrutura de Arquivos

```
backend/
├── app.py        ← Servidor principal (rotas, autenticação, lógica)
├── seed.py       ← Popula o banco com produtos e dados de exemplo
├── README.md     ← Este arquivo
└── mercado_gama.db  ← Criado automaticamente ao rodar
```

---

## ▶️ Como Rodar

### 1. Instale o Flask
```bash
pip install flask
```

### 2. Inicie o servidor
```bash
python app.py
```

O banco de dados `mercado_gama.db` é criado automaticamente com todos os
produtos e dados de exemplo já inseridos.

Acesse: **http://localhost:5000**

---

## 👤 Usuários de Teste

| E-mail                  | Senha    |
|-------------------------|----------|
| ana@exemplo.com         | senha123 |
| carlos@exemplo.com      | senha123 |

---

## 🗄️ Banco de Dados — Tabelas

| Tabela                    | O que armazena                              |
|---------------------------|---------------------------------------------|
| `usuarios`                | Contas, senhas (hash), endereços            |
| `produtos`                | Catálogo completo com marcas e categorias   |
| `pedidos`                 | Pedidos com endereço, frete e status        |
| `itens_pedido`            | Produtos de cada pedido com preço e qty     |
| `historico_visualizacoes` | Base para o sistema de recomendações        |
| `notificacoes`            | Promoções, novidades e novas unidades       |
| `notificacoes_lidas`      | Controla quais notificações cada user leu   |

---

## 🔌 Endpoints da API

### Autenticação

#### `POST /api/cadastro`
Cria uma nova conta.
```json
{
  "nome":      "João Silva",
  "email":     "joao@email.com",
  "senha":     "minhasenha",
  "telefone":  "(11) 99999-0000",
  "endereco":  "Rua das Flores, 100 - Taboão da Serra/SP"
}
```

#### `POST /api/login`
Faz login e inicia sessão.
```json
{
  "email": "ana@exemplo.com",
  "senha": "senha123"
}
```

#### `POST /api/logout`
Encerra a sessão. *(Requer login)*

---

### Perfil

#### `GET /api/perfil`
Retorna dados do usuário logado + estatísticas de compras. *(Requer login)*

**Resposta:**
```json
{
  "usuario": {
    "id": 1,
    "nome": "Ana Gama",
    "email": "ana@exemplo.com",
    "telefone": "(11) 99999-0001",
    "endereco": "Rua das Flores, 100 - Taboão da Serra/SP",
    "criado_em": "2025-01-10 14:30:00",
    "ultimo_login": "2025-01-15 09:12:00"
  },
  "estatisticas": {
    "total_pedidos": 3,
    "total_gasto": 187.50
  },
  "ultimo_pedido": {
    "id": 5,
    "status": "entregue",
    "total": 62.40,
    "criado_em": "2025-01-14 18:00:00"
  }
}
```

#### `PUT /api/perfil`
Atualiza nome, telefone ou endereço. *(Requer login)*
```json
{
  "nome":     "Ana Paula Gama",
  "telefone": "(11) 98888-0001"
}
```

---

### Produtos

#### `GET /api/produtos`
Lista todos os produtos ativos.  
Parâmetros opcionais: `?categoria=bebidas` · `?busca=coca`

**Resposta:**
```json
[
  {
    "id": 31,
    "nome": "Refrigerante 2L",
    "marca": "Coca-Cola",
    "categoria": "bebidas",
    "preco": 9.90,
    "unidade": "/un",
    "emoji": "🥤",
    "estoque": 150
  }
]
```

#### `GET /api/produtos/<id>`
Retorna detalhes de um produto específico.

#### `GET /api/recomendacoes`
Recomenda produtos baseado no histórico de compras do usuário. *(Requer login)*  
Parâmetro opcional: `?limite=6`

**Como funciona:**
- Identifica as categorias mais compradas pelo usuário
- Retorna produtos dessas categorias que ele ainda não comprou
- Se for novo (sem histórico), retorna os produtos mais vendidos no geral

---

### Pedidos

#### `POST /api/pedidos`
Cria um novo pedido. *(Requer login)*
```json
{
  "endereco_entrega": "Rua das Flores, 100 - Taboão da Serra/SP",
  "distancia_km": 4.2,
  "frete": 2.50,
  "itens": [
    { "produto_id": 47, "quantidade": 2 },
    { "produto_id": 49, "quantidade": 1 },
    { "produto_id": 17, "quantidade": 4 }
  ],
  "observacao": "Sem campainha, ligar ao chegar"
}
```

**Status possíveis de um pedido:**

| Status         | Significado               |
|----------------|---------------------------|
| `pendente`     | Aguardando confirmação     |
| `confirmado`   | Confirmado pelo mercado    |
| `em_preparo`   | Sendo separado             |
| `saiu_entrega` | Saiu para entrega          |
| `entregue`     | Entregue com sucesso       |
| `cancelado`    | Cancelado                  |

#### `GET /api/pedidos`
Lista todos os pedidos do usuário com seus itens. *(Requer login)*

#### `GET /api/pedidos/<id>`
Detalhe de um pedido específico. *(Requer login)*

---

### Notificações

#### `GET /api/notificacoes`
Retorna notificações (promoções, novidades, novas unidades). *(Requer login)*

**Resposta:**
```json
{
  "notificacoes": [
    {
      "id": 1,
      "titulo": "🎉 Promoção da Semana!",
      "mensagem": "Frango Seara e Sadia com 15% de desconto...",
      "tipo": "promocao",
      "criado_em": "2025-01-15 08:00:00",
      "lida": 0
    }
  ],
  "nao_lidas": 3
}
```

**Tipos de notificação:** `geral` · `promocao` · `novidade` · `nova_unidade`

#### `POST /api/notificacoes/<id>/ler`
Marca uma notificação como lida. *(Requer login)*

---

## 🔐 Segurança das Senhas

As senhas **nunca são armazenadas em texto puro**.  
O sistema usa **PBKDF2-HMAC-SHA256** com salt aleatório de 16 bytes e
260.000 iterações — o mesmo padrão recomendado pelo NIST para aplicações
em produção.

---

## 🚀 Próximos Passos (para produção)

| O que melhorar        | Como                                     |
|-----------------------|------------------------------------------|
| Banco de dados        | Migrar SQLite → PostgreSQL               |
| Autenticação          | Adicionar JWT para apps mobile           |
| Senhas                | Usar biblioteca `bcrypt` ou `argon2`     |
| Variáveis sensíveis   | Usar arquivo `.env` com `python-dotenv`  |
| Deploy                | Railway, Render ou VPS com Nginx         |
| Pagamentos            | Integrar API do Mercado Pago             |
| E-mails               | Integrar SendGrid para notificações      |
| Recomendações         | Evoluir para ML com scikit-learn         |