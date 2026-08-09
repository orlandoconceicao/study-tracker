# Study Tracker

Aplicação fullstack para acompanhar estudos diários. O back-end usa Django REST Framework e PostgreSQL; o front-end usa React com Vite.

## Estrutura

```text
.
├── backend/                 # Django, Celery, testes e dependências Python
│   ├── config/
│   ├── notifications/
│   ├── studies/
│   ├── tests/
│   ├── users/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # React/Vite
│   ├── public/
│   ├── src/
│   └── package.json
├── .gitignore
├── docker-compose.yml
└── README.md
```

`users` contém o usuário customizado e autenticação. `studies` concentra registros, filtros e serviços de calendário/estatísticas. `notifications` armazena as preferências e tarefas de lembrete. As rotas e regras de negócio não foram alteradas pela reorganização.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register/` | Cria a conta |
| POST | `/api/auth/login/` | Retorna access e refresh JWT |
| POST | `/api/auth/refresh/` | Renova o access token |
| GET | `/api/auth/me/` | Usuário autenticado |
| GET, POST | `/api/studies/` | Lista/cria estudos |
| GET, PUT, PATCH, DELETE | `/api/studies/{id}/` | Opera um estudo próprio |
| GET | `/api/studies/calendar/?month=8&year=2026` | Dias e minutos do mês |
| GET | `/api/studies/statistics/` | Totais e sequências |
| GET, PATCH | `/api/notifications/settings/` | Lembrete do usuário |

Use `Authorization: Bearer <access_token>` nas rotas protegidas. A documentação interativa está em `/api/docs/`.

## Execução local

Back-end (a partir da raiz):

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Preencha `backend/.env` antes de iniciar. O Django lê esse arquivo com base no novo diretório do projeto.

Front-end, em outro terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Por padrão, `VITE_API_URL` aponta para `http://localhost:8000/api`. O back-end aceita, em desenvolvimento, as origens locais nas portas `5173` e `5174`, tanto com `localhost` quanto com `127.0.0.1`.

## Docker

O Compose permanece na raiz e usa `backend/` e `frontend/` como contextos de build separados:

```bash
docker compose --env-file backend/.env up --build
```

Ele inicia PostgreSQL, Redis, Django, Vite, Celery Worker e Celery Beat. Para validar a configuração sem iniciar containers:

```bash
docker compose --env-file backend/.env config --quiet
```

## Testes e verificações

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest

cd ..\frontend
npm test
npm run build
```

Serviços locais: front-end em http://localhost:5173, back-end em http://localhost:8000 e Swagger em http://localhost:8000/api/docs/.
