# Study Tracker API

API REST para acompanhar estudos diários, construída com Django REST Framework e PostgreSQL.

## Arquitetura

`users` contém o usuário customizado e autenticação. `studies` concentra registros, filtros e serviços de calendário/estatísticas. `notifications` armazena a preferência de lembrete, pronta para ser consumida futuramente por Celery + Redis. As views só fazem a orquestração HTTP; regras de agregação ficam em `studies/services.py`.

Relações: `User 1:N Study` e `User 1:1 UserNotificationSettings`.

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

Use `Authorization: Bearer <access_token>` em todas as rotas protegidas. A documentação interativa está em `/api/docs/`.

## Execução

1. Crie um ambiente virtual e instale `pip install -r requirements.txt`.
2. Copie `.env.example` para `.env` e informe credenciais PostgreSQL.
3. Execute `python manage.py makemigrations` e `python manage.py migrate`.
4. Inicie com `python manage.py runserver`.

Filtros disponíveis em estudos: `start_date`, `end_date`, `subject`, `month` e `year`.

## Executando com Docker

1. Copie `.env.example` para `.env` e ajuste as variáveis necessárias. Para o envio de e-mails, informe as credenciais SMTP somente no `.env`.
2. Inicie todos os serviços:

   ```bash
   docker compose up --build
   ```

O Docker Compose inicia PostgreSQL, Redis, Django, Vite, Celery Worker e Celery Beat. Dentro dos containers, Django acessa o banco pelo serviço `db` e o broker pelo serviço `redis`; essas configurações são aplicadas pelo Compose sem alterar o seu `.env` local.

## Testes automatizados

Instale as dependências de desenvolvimento do backend:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Execute os testes e a cobertura do backend:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest --cov --cov-report=term-missing --cov-report=html
```

No frontend, instale as dependências e execute a suíte:

```powershell
cd frontend
npm install
npm test
npm run test:coverage
```

Os testes usam SQLite em memória, backend de e-mail local e mocks para integrações; PostgreSQL, Redis e SMTP não precisam estar ativos.

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/api/docs/

Para parar os serviços, use `docker compose down`. Os dados do PostgreSQL permanecem no volume `postgres_data`; para removê-los intencionalmente, use `docker compose down -v`.

Para acompanhar os logs, use:

```bash
docker compose logs -f
docker compose logs -f backend celery_worker celery_beat
```
