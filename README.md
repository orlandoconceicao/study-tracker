# Study Tracker

Plataforma educacional para registrar e acompanhar estudos, organizar conteúdo curricular e disponibilizar recursos de turmas, exercícios e avaliações. O núcleo do projeto é uma API REST em Django REST Framework e PostgreSQL; a interface React consome essa API para oferecer autenticação, acompanhamento de sessões, calendário, estatísticas, lembretes e configurações.

O repositório demonstra principalmente competências de desenvolvimento backend: modelagem de dados, autenticação JWT, autorização, construção de APIs, processamento assíncrono e execução em containers.

## Sobre o projeto

O Study Tracker centraliza o histórico de estudos e transforma os registros em informações como tempo acumulado, frequência e sequências de dias estudados. O backend também possui um domínio educacional para estruturar currículos, disponibilizar aulas e exercícios, registrar progresso e organizar professores e alunos em turmas.

Atualmente, a aplicação web concentra a experiência de acompanhamento individual. Os recursos educacionais mais amplos estão disponíveis pela API e pelo Django Admin, conforme as permissões de cada usuário.

## Principais funcionalidades

### Conta e acompanhamento de estudos

- Cadastro, login e renovação de sessão com tokens JWT.
- Consulta e atualização do perfil, alteração de senha e desativação da própria conta.
- Cadastro, edição, consulta, filtros e exclusão de sessões do usuário autenticado.
- Calendário mensal com dias estudados e minutos acumulados.
- Estatísticas de tempo, média diária e sequências atual e histórica.
- Preferências de tema, idioma e meta diária.

### Lembretes

- Configuração de lembrete diário por e-mail, horário e fuso horário.
- Processamento periódico com Celery e Redis.
- Controle para evitar mais de um envio no mesmo dia local.

### Conteúdo educacional

- Currículo organizado por nível de ensino, série, matéria, unidade e conteúdo.
- Aulas, exemplos e exercícios de múltipla escolha, verdadeiro ou falso e resposta curta.
- Registro de conclusão de aulas, tentativas e progresso por conteúdo.
- Usuários comuns acessam conteúdo publicado; escritas no currículo exigem usuário `staff`.

### Professores, alunos e turmas

- Perfil educacional de professor ou aluno.
- Criação de turmas por professores e ingresso de alunos por código.
- Atividades vinculadas a conteúdos e acompanhamento do desempenho dos integrantes.
- Administração da turma restrita ao professor responsável.

### Exercícios e avaliações

- Banco de questões com filtros curriculares, dificuldade e tipo.
- Avaliação diagnóstica baseada nos exercícios cadastrados.
- Atividades com início, armazenamento de respostas, entrega e resultados.
- Respostas e progresso vinculados ao usuário autenticado.

## Tecnologias

### Backend

- Python, Django 5 e Django REST Framework
- Simple JWT, django-filter e drf-spectacular
- Celery

### Frontend

- React 18, React Router, Vite e Axios

### Banco de dados

- PostgreSQL 16 na configuração Docker
- Psycopg

### Infraestrutura

- Docker e Docker Compose
- Redis 7
- Celery Worker e Celery Beat

### Testes

- pytest, pytest-django, pytest-cov e Factory Boy no backend
- Vitest, Testing Library e jsdom no frontend

## Arquitetura

```text
React + Vite
     |
     | HTTP / JSON
     v
Django REST Framework ----> PostgreSQL
     |
     +--> Celery Worker <--> Redis
              ^
              |
         Celery Beat
```

O frontend é um cliente separado da API. O Django REST Framework concentra autenticação, validação, permissões e regras da aplicação, e o PostgreSQL persiste os dados. O Celery Beat agenda a verificação dos lembretes; o worker executa as tarefas usando o Redis.

## Segurança

- A API usa JWT, com access token de 30 minutos e refresh token de 7 dias.
- As rotas são autenticadas por padrão; cadastro, login e renovação são as exceções públicas necessárias.
- Estudos, preferências, progresso e avaliações são consultados a partir do usuário autenticado.
- Turmas só podem ser administradas pelo professor responsável, inclusive os relatórios de desempenho.
- A listagem de exercícios não serializa o gabarito; a correção é retornada pelas operações específicas de resposta ou revelação.
- Escritas no currículo exigem usuário `staff`; usuários comuns consultam apenas conteúdo publicado.
- CORS, origens CSRF confiáveis, hosts, banco, e-mail, Redis e chaves são configurados por ambiente.

## API

A API está organizada em autenticação, conta, estudos, notificações, currículo, progresso, turmas, diagnóstico, banco de questões e atividades. Durante a execução local, o Swagger fica em `http://localhost:8000/api/docs/` e o schema OpenAPI em `/api/schema/`.

[Documentação completa da API](docs/API.md)

## Estrutura do projeto

```text
study-tracker/
|-- backend/              # API Django, Celery e testes Python
|   |-- config/           # Configurações, URLs e Celery
|   |-- education/        # Currículo, exercícios, turmas e avaliações
|   |-- notifications/    # Preferências e lembretes
|   |-- studies/          # Registros, calendário e estatísticas
|   `-- users/            # Usuário, autenticação e preferências
|-- frontend/             # Aplicação React/Vite e testes
|-- docs/                 # Documentação complementar
|-- docker-compose.yml
`-- README.md
```

## Executando o projeto

### Pré-requisitos

- Python compatível com `backend/requirements.txt`
- Node.js e npm compatíveis com o projeto Vite
- PostgreSQL e, para os lembretes, Redis
- ou Docker com Docker Compose

O repositório não fixa versões de Python, Node.js, npm ou Docker; por isso, esta documentação não informa versões específicas desses programas.

### Backend

No PowerShell, a partir da raiz:

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Antes das migrations, preencha `backend/.env` com `SECRET_KEY` e os dados do PostgreSQL (`DATABASE_NAME`, `DATABASE_USER` e `DATABASE_PASSWORD`). O backend será servido em `http://localhost:8000`.

### Frontend

Em outro terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Por padrão, `VITE_API_URL` aponta para `http://localhost:8000/api`, e o Vite atende em `http://localhost:5173`.

### Docker

Copie `backend/.env.example` para `backend/.env` e defina valores não vazios para `SECRET_KEY` e `DATABASE_PASSWORD`. Depois execute:

```bash
docker compose --env-file backend/.env up --build
```

O Compose inicia PostgreSQL, Redis, backend, frontend, Celery Worker e Celery Beat. Para apenas validar a configuração:

```bash
docker compose --env-file backend/.env config --quiet
```

## Variáveis de ambiente

Os arquivos `.env.example` documentam os nomes esperados sem fornecer credenciais:

- Aplicação: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`.
- PostgreSQL: `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST` e `DATABASE_PORT`.
- E-mail: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `DEFAULT_FROM_EMAIL`.
- Processamento: `CELERY_BROKER_URL` e, opcionalmente, `CELERY_RESULT_BACKEND`.
- Frontend: `VITE_API_URL`.

Não versione arquivos `.env` nem credenciais reais.

## Testes

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest
```

Os testes atuais verificam autenticação e tokens, isolamento de dados, conta e preferências, CRUD de estudos, filtros, calendário, estatísticas, configuração e processamento de lembretes.

Frontend:

```powershell
cd frontend
npm test
npm run build
```

Os testes cobrem autenticação, contexto de sessão, dashboard, estudos, calendário, estatísticas, configurações, tema e serviços HTTP.

## Autor

**Orlando Conceição Vilhalba de Almeida**

Desenvolvedor Backend em formação, com foco em Python, Django, Django REST Framework, PostgreSQL, APIs REST e Docker, utilizando React como tecnologia complementar para integração das aplicações.

GitHub: [github.com/orlandoconceicao](https://github.com/orlandoconceicao)

LinkedIn: [linkedin.com/in/orlando-conceição-582234315](https://www.linkedin.com/in/orlando-concei%C3%A7%C3%A3o-582234315)

Portfólio: [orlandoconceicao.github.io](https://orlandoconceicao.github.io)
