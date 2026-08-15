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

## Módulo educacional

O app Django `education` organiza o currículo na hierarquia nível de ensino → série → matéria da série → unidade → conteúdo → aula/exercício. Textos de aula são armazenados como texto simples em `TextField`; a aplicação não persiste HTML renderizável.

Usuários autenticados podem consultar o currículo, concluir aulas e responder exercícios. A resposta correta e a explicação não aparecem na consulta do exercício e são reveladas somente após uma tentativa. Usuários `staff` administram o currículo pelo Django Admin (ou pelas operações de escrita da API); usuários comuns recebem `403` nessas operações.

O progresso de um conteúdo considera uma parte para cada aula concluída e duas para cada exercício: uma pela tentativa e outra pelo acerto. Ele é recalculado em `education/services.py` após concluir uma aula ou responder um exercício.

### Professores, alunos e turmas

Em `/classes`, cada usuário escolhe seu perfil educacional como aluno ou professor, sem alterar sua conta ou autenticação. Professores criam turmas vinculadas a uma série, compartilham o código de seis caracteres, publicam atividades referenciando conteúdos existentes e acompanham o desempenho dos alunos. Alunos entram com o código, acessam matérias e atividades e podem sair da turma. Dados de colegas e relatórios de desempenho são visíveis somente ao professor proprietário.

### Avaliação diagnóstica

Antes de estudar um conteúdo, o aluno pode iniciar um diagnóstico de até dez questões reutilizadas do banco de exercícios. As respostas corretas não são enviadas durante a avaliação. Ao final, regras determinísticas classificam o resultado como iniciante, intermediário ou avançado, agrupam pontos fortes e conteúdos para revisão pelas aulas associadas e recomendam uma aula para começar.

### Banco de Questões e atividades

O Banco de Questões em `/questions` reutiliza `Exercise` e permite filtrar pela hierarquia curricular, dificuldade e tipo. Professores podem selecionar questões e criar atividades para suas turmas. Alunos acessam as listas em `/activities`, respondem sem receber o gabarito antes da entrega e recebem ao final quantidade de questões, acertos, erros, percentual e tempo utilizado. O professor criador pode consultar os resultados dos alunos.

### Revisão e Caderno de Erros

As páginas `/review` e `/review/errors` transformam o histórico existente de `ExerciseAttempt` em uma fila de revisão e um caderno de questões erradas. A prioridade é calculada deterministicamente com quantidade de erros, percentual de acerto, tempo desde a última tentativa e progresso do conteúdo. Refazer uma questão sempre cria uma nova tentativa e preserva o histórico anterior.

### Recomendações de estudo e ensino

“O que estudar agora?” usa tentativas, progresso, diagnósticos, aulas concluídas e entregas de atividades para priorizar conteúdos sem IA externa. A recomendação principal aparece no Dashboard. Professores acessam `/teaching` para consultar “O que ensinar agora?” por turma e aluno e montar um roteiro determinístico com revisão, explicação, exemplo, exercício guiado, prática independente, correção e resumo. O roteiro utiliza apenas aulas e exercícios cadastrados e sinaliza etapas sem material.

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
| GET | `/api/education/levels/` | Lista níveis de ensino |
| GET | `/api/education/grades/` | Lista séries |
| GET | `/api/education/subjects/` | Lista matérias ativas |
| GET | `/api/education/grades/{id}/subjects/` | Matérias de uma série |
| GET | `/api/education/subjects/{id}/units/?grade={id}` | Unidades da matéria, opcionalmente por série |
| GET | `/api/education/topics/{id}/` | Detalha um conteúdo |
| GET | `/api/education/topics/{id}/lessons/` | Aulas do conteúdo |
| GET | `/api/education/topics/{id}/exercises/` | Exercícios sem gabarito |
| GET | `/api/education/lessons/{id}/` | Detalha uma aula |
| POST | `/api/education/lessons/{id}/complete/` | Marca a aula como concluída |
| POST | `/api/education/exercises/{id}/answer/` | Registra resposta e retorna a correção |
| GET | `/api/education/progress/` | Progresso do usuário autenticado |
| GET, PATCH | `/api/education/profile/` | Consulta ou escolhe o perfil educacional |
| GET, POST | `/api/education/classrooms/` | Lista turmas acessíveis ou cria uma turma |
| GET, PATCH, DELETE | `/api/education/classrooms/{id}/` | Consulta ou administra uma turma própria |
| POST | `/api/education/classrooms/join/` | Entra em uma turma usando o código |
| POST | `/api/education/classrooms/{id}/join/` | Entra em uma turma pelo identificador |
| POST | `/api/education/classrooms/{id}/leave/` | Sai de uma turma |
| GET, POST | `/api/education/classrooms/{id}/activities/` | Lista ou publica atividades |
| GET | `/api/education/classrooms/{id}/performance/` | Desempenho dos alunos para o professor |
| POST | `/api/education/topics/{id}/diagnostic/start/` | Inicia um diagnóstico do conteúdo |
| POST | `/api/education/diagnostics/{id}/answer/` | Responde uma questão do diagnóstico |
| POST | `/api/education/diagnostics/{id}/finish/` | Finaliza e calcula o diagnóstico |
| GET | `/api/education/diagnostics/{id}/result/` | Consulta o resultado do próprio diagnóstico |
| GET | `/api/education/questions/` | Banco de questões com filtros curriculares |
| GET, POST | `/api/education/assignments/` | Lista ou cria atividades |
| GET, PATCH, DELETE | `/api/education/assignments/{id}/` | Consulta ou administra uma atividade |
| POST | `/api/education/assignments/{id}/start/` | Inicia ou retoma uma entrega |
| GET | `/api/education/assignments/{id}/results/` | Resultados disponíveis ao professor criador |
| POST | `/api/education/student-assignments/{id}/answer/` | Salva uma resposta sem revelar a correção |
| POST | `/api/education/student-assignments/{id}/submit/` | Entrega e calcula o resultado |
| GET | `/api/education/review/` | Fila de conteúdos priorizados para revisão |
| GET | `/api/education/review/errors/` | Caderno de exercícios respondidos incorretamente |
| GET | `/api/education/recommendations/` | Recomendações do usuário autenticado |
| GET | `/api/education/recommendations/?classroom={id}&student={id}` | Recomendações do aluno para o professor autorizado |
| GET | `/api/education/recommendations/lesson-plan/?topic={id}&classroom={id}` | Roteiro com materiais existentes |

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

## Autor

**Orlando Conceição Vilhalba de Almeida**

Desenvolvedor Backend em formação, com foco em Python, Django REST Framework, PostgreSQL e Docker, desenvolvendo também interfaces em React para integração com APIs.

GitHub: [orlandoconceicao](https://github.com/orlandoconceicao)
