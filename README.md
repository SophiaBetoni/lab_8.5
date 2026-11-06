# Leitor — MVP (arquitetura Cliente-Servidor)

App de controle de leituras (estilo Letterboxd para livros). Livros organizados em
**lidos / lendo / quero ler**, com nota, login, perfil e top 3 favoritos.

```
livraria/
├── backend/    # Servidor: API REST (FastAPI + SQLAlchemy)
└── frontend/   # Cliente: HTML + JS puro, só consome a API
```

O cliente e o servidor são independentes e se comunicam apenas por HTTP/JSON.

## Como rodar localmente

### 1. Back-end
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API em http://127.0.0.1:8000 — documentação interativa em http://127.0.0.1:8000/docs

### 2. Front-end
Abra a pasta `frontend/` no VS Code, clique com o botão direito em `index.html` e
escolha **Open with Live Server** (extensão *Live Server*). Ou rode:
```bash
cd frontend
python -m http.server 5500
```
e acesse http://127.0.0.1:5500

## Endpoints

| Método | Rota                    | Descrição                          |
|--------|-------------------------|------------------------------------|
| POST   | /auth/registro          | Cria conta e devolve o token       |
| POST   | /auth/login             | Login e devolve o token            |
| GET    | /livros?q=              | Lista/busca livros do catálogo     |
| POST   | /livros                 | Cadastra livro (autenticado)       |
| GET    | /minha-lista?status=    | Lista as leituras do usuário       |
| POST   | /minha-lista            | Adiciona livro à lista             |
| PATCH  | /minha-lista/{id}       | Muda status, nota ou favorito      |
| DELETE | /minha-lista/{id}       | Remove da lista                    |
| GET    | /perfil                 | Resumo e top 3 favoritos           |

Rotas autenticadas usam o cabeçalho `Authorization: Bearer <token>`.

## Variáveis de ambiente (back-end)

- `DATABASE_URL`: URL do banco. Padrão: SQLite local (`livraria.db`). No deploy, use PostgreSQL.
- `ALLOWED_ORIGINS`: URL(s) do front-end liberadas no CORS, separadas por vírgula. Padrão: `*`.


