# Guia completo do Study Tracker

> Auditoria técnica e didática do código existente no workspace em 23/08/2026. As afirmações abaixo vêm dos arquivos do repositório; quando não há evidência, isso é indicado explicitamente. Valores secretos não são reproduzidos.

## 1. Visão geral

O **Study Tracker** é uma plataforma educacional com dois domínios relacionados:

1. acompanhamento pessoal de estudos: conta, sessões de estudo, calendário, estatísticas, preferências e lembretes por e-mail;
2. educação estruturada: currículo, aulas, exercícios, progresso, diagnóstico, turmas e atividades.

O frontend implementado atende principalmente ao primeiro domínio. O segundo está disponível pela API REST e pelo Django Admin, mas não possui telas React no código atual. Os usuários esperados são estudantes que acompanham a rotina e, no domínio educacional, alunos e professores.

### Stack comprovada

| Camada | Tecnologia | Evidência/versão declarada |
| --- | --- | --- |
| Backend | Python, Django, Django REST Framework | Python 3.13 na imagem; Django `>=5.1,<6`; DRF `>=3.15,<4` |
| Autenticação | Simple JWT | `>=5.3,<6` |
| Banco | PostgreSQL + psycopg | PostgreSQL 16 Alpine no Compose; psycopg `>=3.2,<4` |
| Filtros/schema | django-filter, drf-spectacular | requirements e `config/settings.py` |
| Assíncrono | Celery + Redis | Celery `>=5.4,<6`; Redis 7 Alpine |
| Frontend | React 18, JavaScript, React Router 6, Axios, Vite 6 | `frontend/package.json` |
| Testes | pytest/pytest-django; Vitest/Testing Library/jsdom | requirements-dev e package.json |
| Containers | Docker e Docker Compose | dois Dockerfiles e `docker-compose.yml` |

Não há TypeScript, Redux, Zustand, React Query, WebSockets, Django Channels, upload de mídia, rate limiting ou cache de aplicação implementados.

## 2. Arquitetura e fluxo de dados

```text
NAVEGADOR
  │ React 18 + BrowserRouter
  │ Axios / JSON / Authorization: Bearer <access>
  ▼
DJANGO REST FRAMEWORK (WSGI, porta 8000)
  ├── users ───────── conta, JWT e preferências
  ├── studies ─────── CRUD, calendário e estatísticas
  ├── notifications ─ configurações e envio de e-mail
  └── education ───── currículo, progresso, turmas e avaliações
          │ ORM / transações
          ▼
      POSTGRESQL

CELERY BEAT ── a cada 60 s ──► REDIS ──► CELERY WORKER
                                           │
                                           └── SMTP (lembrete por e-mail)
```

Uma requisição típica entra pelo `baseURL` de `frontend/src/services/api.js`, recebe o JWT no interceptor, chega a `backend/config/urls.py`, é encaminhada ao `urls.py` do app e então a uma view/viewset. O serializer valida JSON e converte entre representação e model. A view aplica permissões e chama ORM ou service; o ORM persiste no PostgreSQL. DRF serializa a resposta JSON e o componente atualiza estado React local/contextual.

O backend é WSGI: existe `config/wsgi.py`, mas não `asgi.py`. Não há Channels nem conexão WebSocket.

## 3. Estrutura de diretórios

```text
study-tracker/
├── backend/
│   ├── config/          # settings, URL raiz, WSGI e app Celery
│   ├── users/           # usuário customizado, conta e preferências
│   ├── studies/         # sessões, filtros, estatísticas e calendário
│   ├── notifications/   # preferências, e-mail e tarefa Celery
│   ├── education/       # currículo, aulas, exercícios, turmas e avaliações
│   │   ├── management/commands/ # seed, importação e auditoria curricular
│   │   ├── migrations/
│   │   └── seed_data/   # JSON curricular/BNCC
│   ├── tests/           # suíte pytest principal
│   ├── manage.py
│   ├── requirements*.txt
│   ├── pytest.ini
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/  # layout, autenticação, dashboard e calendário
│   │   ├── context/     # AuthContext
│   │   ├── hooks/       # useAuth
│   │   ├── pages/       # estudos, formulário, estatísticas, configurações
│   │   ├── services/    # Axios, estudos e tema
│   │   ├── styles/
│   │   └── test/        # setup e render auxiliar
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/                # referência de API e conteúdo educacional
├── docker-compose.yml
├── README.md
└── .gitignore
```

Artefatos ignorados (`node_modules`, `.venv`, `dist`, caches e cobertura) não fazem parte da arquitetura. A pasta local `.vercel/` está não rastreada e contém apenas vínculo da máquina com um projeto Vercel; não é configuração reproduzível do repositório.

## 4. Inicialização e configuração do backend

`backend/manage.py` define `DJANGO_SETTINGS_MODULE=config.settings` e delega comandos ao Django. `config/settings.py` carrega `backend/.env` com `python-dotenv`, registra apps/middleware, banco, REST, JWT, CORS, e-mail e Celery. `config/urls.py` monta todas as URLs. `config/wsgi.py` cria a aplicação WSGI usada por servidores compatíveis; nenhum servidor de produção como Gunicorn está declarado. `config/celery.py` cria a aplicação Celery, importa opções com prefixo `CELERY_` e autodetecta `tasks.py`. `config/__init__.py` expõe essa aplicação como `celery_app`.

### Ciclo de request

1. `SecurityMiddleware`, sessão, CORS, common, CSRF, autenticação, messages e clickjacking são executados nessa ordem.
2. O resolver usa `config.urls`.
3. DRF tenta `JWTAuthentication`; por padrão exige `IsAuthenticated`.
4. View/viewset seleciona serializer, queryset e permissões específicas.
5. Serializers chamam validações e models/services usam ORM.
6. DRF retorna JSON e status HTTP. Não existe exception handler customizado: valem respostas padrão de Django/DRF.

`config/settings_test.py` troca PostgreSQL por SQLite em memória, usa hasher MD5 para acelerar testes, backend de e-mail em memória e tarefas Celery eager.

## 5. Apps, models e banco de dados

### 5.1 `users`

Arquivos centrais: `users/models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`.

- `User` herda `AbstractUser`: mantém username, senha hasheada, nomes, flags e datas do Django; redefine `email` como único. `AUTH_USER_MODEL = "users.User"` deve ser usado em relações.
- `UserPreferences`: `user` OneToOne com cascade e `related_name=preferences`; `theme` (`light`, `dark`, `system`, padrão `system`); único idioma aceito `pt-BR`; meta diária positiva, padrão 60. O serializer restringe a meta a 1–1440 minutos.

`RegisterSerializer` aceita `username`, `email`, senha mínima de oito caracteres e chama `create_user`, portanto a senha é hasheada. `UserSerializer` expõe perfil, mas nunca senha/flags administrativas; e-mail é comparado sem diferenciar maiúsculas. `ChangePasswordSerializer` exige senha atual, confirmação e executa `validate_password`. Entretanto `AUTH_PASSWORD_VALIDATORS=[]`, então além do `min_length=8` não há validadores globais ativos. `DeleteAccountSerializer` exige senha e a frase exata; a conta é apenas desativada (`is_active=False`), não apagada.

### 5.2 `studies`

`Study` possui:

| Campo | Tipo/regra |
| --- | --- |
| `user` | ForeignKey para User, cascade, `related_name=studies` |
| `date` | DateField, indexado, obrigatório |
| `duration_minutes` | PositiveInteger, mínimo 1 |
| `subject` | CharField(255), indexado |
| `notes` | TextField opcional |
| `created_at`, `updated_at` | timestamps automáticos |

Ordena por data e criação decrescentes e possui índice composto `(user,date)`. `StudyViewSet.get_queryset()` filtra sempre pelo usuário; `perform_create()` injeta o dono. `IsStudyOwner` repete a proteção por objeto. `StudyFilter` oferece `start_date`, `end_date`, `month`, `year` e `subject__icontains`.

`calendar_summary` agrega `Sum(duration_minutes)` por data e devolve todos os dias do mês. `study_statistics` calcula horas totais, dias distintos, média por dia estudado, minutos na semana/mês e sequências consecutivas. A sequência atual é válida se o último estudo foi hoje ou ontem.

### 5.3 `notifications`

`UserNotificationSettings` é OneToOne com User: `enabled=False`, hora opcional, timezone padrão `America/Cuiaba` e `last_reminder_sent` interno. O serializer valida o timezone com `zoneinfo` e exige hora ao habilitar.

`send_study_reminder` usa `django.core.mail.send_mail`, destinatário igual ao e-mail atual do usuário e versões texto/HTML. A task `check_study_reminders` seleciona configurações habilitadas com usuário relacionado, converte o horário UTC atual para o fuso individual, ignora horários futuros, e-mail ausente/fuso inválido e envio já realizado no dia local. Se o scheduler atrasar, envia mais tarde no mesmo dia; só grava `last_reminder_sent` após sucesso. Falhas são registradas por `logger`.

### 5.4 `education`: currículo global

`OrderedModel` é abstrato e adiciona `order` indexado. Os models curriculares são:

- `Curriculum`: nome, versão, fonte, URL, região (Brasil), ativo; unicidade `(name,version,region)`.
- `EducationLevel`: nome, slug globalmente único, ordem.
- `Grade`: nível FK cascade, nome, slug; slug único dentro do nível.
- `Subject`: nome, slug único, descrição/ícone opcionais, ordem, ativo.
- `GradeSubject`: série + matéria, currículo opcional protegido, ativo; par série/matéria único.
- `Unit`: vínculo série-matéria, título, descrição, ordem.
- `KnowledgeObject`: unidade, currículo protegido, nome/descrição/URL; nome único por unidade.
- `Skill`: currículo protegido, série, matéria, código/descrição/URL; código único por currículo.
- `Topic`: unidade, título/slug/descrição, dificuldade, duração, status, M2M para objetos e habilidades; slug único por unidade.
- `Lesson`: tópico, textos pedagógicos, duração, ordem e status.
- `Example`: aula, problema/passos/resposta/explicação; ordem única por aula.
- `Exercise`: tópico, aula opcional (`SET_NULL`), enunciado, tipo, dificuldade, explicação e status.
- `ExerciseChoice`: exercício, texto, indicador de gabarito e ordem.

Status possíveis são `draft`, `review`, `published`; dificuldades `easy`, `medium`, `hard`; exercícios aceitam `multiple_choice`, `true_false`, `short_answer`. O conteúdo público é global, não duplicado por usuário.

### 5.5 `education`: experiência, turmas e avaliações

- `ExerciseAttempt`: usuário + exercício + resposta JSON + acerto + horário; índice `(user,exercise,attempted_at)`.
- `TopicProgress`: usuário/tópico único, concluído, percentual decimal 0–100, conclusão e último acesso.
- `LessonProgress`: usuário/aula único, concluído e horário.
- `EducationProfile`: OneToOne, papel `student` ou `teacher`.
- `Classroom`: professor, nome, descrição, série protegida, código aleatório único de seis caracteres, ativo, alunos M2M via membership.
- `ClassroomMembership`: turma/aluno único e data de ingresso.
- `ClassroomActivity`: turma e exatamente uma referência entre tópico, aula ou exercício; prazo opcional. A regra existe em `clean()` e no serializer.
- `DiagnosticAssessment`: usuário/tópico, início/fim, nota, percentual e nível (`beginner`, `intermediate`, `advanced`).
- `DiagnosticResponse`: avaliação, exercício protegido, ordem, resposta/acerto/horário; exercício único por diagnóstico.
- `Assignment`: professor, turma opcional, título/descrição, disponibilidade/prazo, exercícios M2M.
- `AssignmentExercise`: atividade/exercício protegido, ordem; par único.
- `StudentAssignment`: atividade/aluno único, início/entrega, nota/percentual.
- `StudentAssignmentResponse`: entrega/exercício protegido, resposta/acerto/horário; par único.

### Diagrama relacional simplificado

```text
User ─1:1─ UserPreferences
 ├─1:1─ UserNotificationSettings
 ├─1:N─ Study
 ├─1:1─ EducationProfile
 ├─1:N─ ExerciseAttempt ─N:1─ Exercise ─N:1─ Topic
 ├─1:N─ TopicProgress ─N:1──── Topic
 ├─1:N─ LessonProgress ─N:1─ Lesson ─N:1─ Topic
 ├─ professor ─1:N─ Classroom ─N:1─ Grade
 │                         └─M:N─ alunos (ClassroomMembership)
 ├─1:N─ DiagnosticAssessment ─N:1─ Topic
 │          └─1:N─ DiagnosticResponse ─N:1─ Exercise
 └─1:N─ StudentAssignment ─N:1─ Assignment ─N:1─ Classroom
             └─1:N─ StudentAssignmentResponse ─N:1─ Exercise

EducationLevel ─1:N─ Grade ─1:N─ GradeSubject ─1:N─ Unit ─1:N─ Topic
Subject ────────1:N──────────┘                      ├─1:N─ Lesson ─1:N─ Example
Curriculum ─1:N─ GradeSubject                      └─1:N─ Exercise ─1:N─ Choice
          ├─1:N─ KnowledgeObject ─M:N─ Topic
          └─1:N─ Skill ───────────M:N─ Topic
```

### PostgreSQL e migrations

Sem `DATABASE_URL`, Django usa `django.db.backends.postgresql` e cinco variáveis separadas. Se `POSTGRES_URL` ou `DATABASE_URL` existir, `dj_database_url.parse` tem prioridade, força SSL, `conn_max_age=0` e representa o caminho indicado para produção/serverless. O driver é psycopg 3.

Migrations ficam em cada `app/migrations`. Há 3 em users, 4 em studies, 2 em notifications e 13 em education. Elas criam tabelas, constraints e índices; as educacionais também incluem dados (`0007_seed_education_levels_and_grades`, `0011_link_existing_subjects_to_all_grades`) e removem o antigo model/campos `Child` em `0013`. Comandos:

```powershell
python manage.py makemigrations --check --dry-run  # detectar mudanças sem migration
python manage.py makemigrations                    # gerar após alteração intencional de model
python manage.py migrate                           # aplicar pendências
python manage.py showmigrations                    # verificar estado
python manage.py sqlmigrate education 0013         # inspecionar SQL de uma migration
```

Faça backup antes de migrations destrutivas em produção; migrations de dados devem ser avaliadas separadamente. O Compose roda `migrate` automaticamente antes do servidor.

## 6. Serializers e regras de serviço educacionais

### O que é

No DRF, serializer define o contrato JSON, valida entrada e converte models em respostas. ModelSerializer deriva campos do model; Serializer explícito representa comandos/DTOs sem tabela própria.

### Neste projeto

Serializers curriculares expõem IDs e metadados aninhados. `TopicSerializer` acrescenta matéria, série, grade-subject e códigos de habilidade. `LessonSerializer` inclui exemplos estruturados. `ExerciseSerializer` remove `explanation` durante o carregamento e usa `PublicExerciseChoiceSerializer`, que omite `is_correct`; gabarito só sai em `answer` ou `reveal`. Ele também exige que a aula pertença ao tópico.

`ClassroomSerializer` mostra alunos somente ao professor dono, embora qualquer membro veja contagem/atividades. `ClassroomActivitySerializer` exige exatamente uma referência e mesma série da turma. `EducationProfileSerializer` impede um professor com turmas de virar aluno.

`DiagnosticAssessmentSerializer` aninha questões sem gabarito; `StudentAssignmentSerializer` só revela `is_correct` depois da entrega. `AssignmentSerializer.create()` delega a `create_assignment`, que valida dono da turma, existência das questões, lista não vazia e série coerente.

Em `education/services.py`, operações sensíveis usam `transaction.atomic`:

- `check_answer`: múltipla escolha compara conjunto de IDs; verdadeiro/falso normaliza variantes; resposta curta faz comparação textual com trim/casefold.
- `record_attempt`: corrige, grava tentativa e recalcula progresso.
- `update_topic_progress`: cada aula concluída vale 1; cada exercício tentado vale 1 e acertado vale mais 1. Percentual = pontos obtidos / (`aulas + 2*exercícios`).
- diagnóstico: seleciona até dez exercícios com gabarito, exige pelo menos cinco, impede resposta repetida, exige todas antes de finalizar e classifica `<50`, `<80`, `>=80`.
- atividade: cria snapshot de respostas ao iniciar; exige membership, disponibilidade e todas as respostas antes da entrega.

## 7. API e roteamento

Todas as rotas abaixo começam em `backend/config/urls.py`. Salvo registro, login e refresh, a permissão global exige JWT.

### Conta

| Método e URL | Entrada / processamento | Resposta |
| --- | --- | --- |
| `POST /api/auth/register/` | username, email, password | usuário criado (201, sem senha) |
| `POST /api/auth/login/` | username, password | `access`, `refresh` |
| `POST /api/auth/refresh/` | refresh | novo access |
| `GET/PATCH /api/auth/me/` | perfil / campos parciais | perfil público |
| `POST /api/auth/change-password/` | current/new/confirm | mensagem de sucesso |
| `DELETE /api/auth/account/` | senha + frase | 204; conta desativada |
| `GET/PATCH /api/users/preferences/` | tema, idioma, meta | preferências |

Não há endpoint de logout/token blacklist. Logout é exclusão local dos tokens.

### Estudos e notificações

| Método e URL | Uso |
| --- | --- |
| `GET/POST /api/studies/` | lista filtrada/criação própria |
| `GET/PUT/PATCH/DELETE /api/studies/{id}/` | CRUD próprio |
| `GET /api/studies/calendar/?month=&year=` | mapa diário do mês |
| `GET /api/studies/statistics/` | agregados e sequências |
| `GET/PATCH /api/notifications/settings/` | configuração do lembrete |
| `POST /api/notifications/test/` | envio SMTP imediato |

### Educação registrada no roteador

Os recursos `levels`, `grades`, `subjects`, `topics`, `lessons` e `exercises` têm CRUD padrão; leitura exige autenticação, escrita também exige `is_staff`. Usuário comum só enxerga assunto ativo e conteúdo publicado.

| Rota adicional | Regra principal |
| --- | --- |
| `GET grades/{id}/subjects/` | vínculos ativos e contagem publicada |
| `GET subjects/{id}/units/?grade=` | unidades, filtráveis por série |
| `GET topics/{id}/lessons/` | aulas publicadas para não staff |
| `GET topics/{id}/exercises/?page=&page_size=` | sem gabarito; paginação só se `page` existir, máximo 50 |
| `GET topics/{id}/progress/` | contagens/acurácia do usuário |
| `POST topics/{id}/diagnostic/start/` | cria diagnóstico |
| `POST lessons/{id}/complete/` | marca aula e recalcula tópico |
| `POST exercises/{id}/answer/` | grava tentativa e revela correção |
| `POST exercises/{id}/reveal/` | revela sem gravar tentativa |
| `GET progress/?topic=&grade_subject=` | progresso próprio |
| `GET/PATCH profile/` | perfil aluno/professor |
| CRUD `classrooms/` | lista apenas turmas próprias/participadas |
| `POST classrooms/join/` | body `{code}`; somente aluno |
| `POST classrooms/{id}/join/`, `leave/` | ingresso/saída |
| `GET/POST classrooms/{id}/activities/` | professor dono cria |
| `GET classrooms/{id}/performance/` | professor dono |
| `POST diagnostics/{id}/answer/`, `finish/` | somente avaliação própria |
| `GET questions/` | banco de questões com filtros level/grade/subject/unit/topic/difficulty/type |
| CRUD `assignments/` | professor cria/altera/remove; aluno da turma lê |
| `POST assignments/{id}/start/` | aluno participante inicia/retoma |
| `GET assignments/{id}/results/` | somente professor |
| `GET student-assignments/{id}/` | entrega própria |
| `POST student-assignments/{id}/answer/`, `submit/` | responder/entregar |

O documento `docs/API.md` menciona `GET diagnostics/{id}/result/`, mas essa action não está na classe registrada `DiagnosticAssessmentViewSet`; o método `result` aparece indevidamente em `RecommendationViewSet`, que nem é registrado. Logo a rota não existe no roteamento real atual.

## 8. Autenticação, autorização e segurança

### JWT neste projeto

O login usa `TokenObtainPairView`: access expira em 30 minutos e refresh em 7 dias. O frontend salva ambos em `localStorage`; o interceptor injeta apenas access. Em qualquer 401, remove os dois e dispara `study-session-expired`, fazendo `AuthContext` limpar o usuário. Apesar de guardar refresh, o frontend **não chama** `/auth/refresh/`: não há renovação automática. Recarregar a aplicação com access válido consulta `/auth/me/` e preferências; access expirado encerra a sessão.

Armazenar JWT em localStorage é funcional, mas torna tokens acessíveis a JavaScript em caso de XSS. Não há cookie HttpOnly, rotação/blacklist ou CSP configurada no repositório.

### Autenticação versus autorização

Autenticação identifica o usuário pelo JWT. Autorização decide o recurso: queryset próprio para estudos/progresso/diagnósticos/entregas; staff para escrita curricular; papel professor para criar turmas/atividades; ownership para alterar turma/atividade e consultar desempenho. A API restringe dados antes da busca, frequentemente fazendo um ID alheio resultar em 404.

Segurança comprovada: hashing Django, validação da senha atual, JWT, isolamento por usuário, CORS explícito, CSRF trusted origins, middleware clickjacking e SSL obrigatório na URL de banco. Ausências relevantes: validadores Django de senha desabilitados, throttling/rate limit, blacklist JWT, headers customizados, handler de auditoria e configuração explícita de cookies/HTTPS proxy.

## 9. Frontend

### Inicialização, rotas e estado

`src/main.jsx` inicializa tema, monta `createRoot`, `BrowserRouter`, `AuthProvider` e `App` sob StrictMode:

```text
main.jsx → BrowserRouter → AuthProvider → App → Routes
                                      └→ Layout → Sidebar + Outlet → Page
```

| Rota | Componente | Acesso/dados |
| --- | --- | --- |
| `/login` | `LoginPage` | pública; login JWT |
| `/register` | `RegisterPage` | pública; cadastro |
| `/dashboard` | `DashboardHome` | Layout protegido; estatísticas, estudos e calendário |
| `/studies` | `Studies` | lista/filtros/exclusão |
| `/studies/new` | `StudyForm` | criação |
| `/studies/:id/edit` | `StudyForm` | detalhe + patch |
| `/statistics` | `Statistics` | agregados |
| `/settings` | `Settings` | perfil, preferências, lembrete, senha e conta |
| qualquer outra | `Navigate` | redireciona a dashboard e então Layout decide login |

Não há páginas para `education`. `Layout` é o guarda de rotas privadas: espera o carregamento do contexto e redireciona se `user` for nulo.

Estado usa `useState`/`useEffect` local e Context API apenas para autenticação/preferências. Não há store global adicional. `useAuth` é um wrapper de `useContext(AuthContext)`.

### Componentes e formulários principais

- `AuthPages`: formulários controlados, valida confirmação no cliente e chama contexto; mensagens de erro são genéricas.
- `DashboardHome`: carrega estatísticas e estudos em paralelo, mostra cinco recentes e incorpora `Calendar`.
- `Calendar`: carrega resumo ao mudar mês e, ao clicar em dia estudado, filtra sessões daquela data.
- `Studies`: lista, filtra por datas/assunto e confirma exclusão.
- `StudyForm`: detecta criação/edição por `useParams`, transforma minutos em número e redireciona à dashboard.
- `Statistics`: exibe seis métricas da API.
- `Settings`: cinco fluxos independentes: perfil, lembrete, senha, preferências e desativação; a validação cliente espelha apenas parte do backend.
- `Sidebar`, `RecentStudies` e `StatCard` são componentes de apresentação reutilizados.

Não existem interfaces/DTOs TypeScript. O contrato é implícito nos objetos JavaScript e deve permanecer alinhado aos serializers manualmente.

### API client

`services/api.js` cria Axios com `VITE_API_URL` ou fallback `http://localhost:8000/api`. URLs de serviço começam com `/`, logo o prefixo `/api` pertence ao baseURL. O request interceptor lê `study_access_token`; o response interceptor trata todos os 401 como sessão expirada. `services/studies.js` centraliza os sete métodos do domínio. Settings/Auth chamam Axios diretamente.

## 10. Fluxos completos

### Cadastro e login

```text
RegisterPage → AuthContext.register → POST /api/auth/register/
→ RegisterView → RegisterSerializer → User.create_user → PostgreSQL → /login

LoginPage → AuthContext.login → POST /api/auth/login/
→ SimpleJWT valida User/senha → access+refresh → localStorage
→ GET /api/auth/me/ + GET /api/users/preferences/ → contexto → /dashboard
```

### Criar e consultar estudo

```text
StudyForm → studiesApi.create → POST /api/studies/
→ JWTAuthentication → StudyViewSet → StudySerializer
→ perform_create(user=request.user) → Study → PostgreSQL
→ dashboard → statistics() + list() → estado React
```

O usuário não envia `user`; ownership é imposto no servidor. Calendário agrega pelo ORM, enquanto estatísticas percorrem as datas distintas em Python para streaks.

### Lembrete diário

```text
Settings → PATCH notifications/settings/ → serializer valida hora/fuso → PostgreSQL
Celery Beat (60 s) → mensagem no Redis → worker → check_study_reminders
→ horário local + deduplicação diária → send_mail → SMTP
→ last_reminder_sent somente após sucesso
```

### Exercício e progresso

```text
cliente API → GET exercise (sem is_correct/explicação)
→ POST exercises/{id}/answer/ {answer}
→ record_attempt → check_answer → ExerciseAttempt
→ update_topic_progress → TopicProgress → resposta com correção/explicação
```

### Atividade escolar

```text
professor cria Assignment + exercise_ids
→ service valida turma/série → AssignmentExercise
aluno membro chama start → StudentAssignment + respostas vazias
→ answer (correção guardada, escondida antes da entrega)
→ submit exige todas → nota/percentual → resultado liberado
```

## 11. Variáveis de ambiente

| Variável | Uso | Local | Produção |
| --- | --- | --- | --- |
| `SECRET_KEY` | chave criptográfica Django | obrigatória de fato; há fallback inseguro | deve ser secreta e forte |
| `DEBUG` | modo debug | example `True` | `False` |
| `ALLOWED_HOSTS` | hosts aceitos | localhost/127.0.0.1 | domínios backend |
| `CORS_ALLOWED_ORIGINS` | origens JS | portas Vite | domínio frontend |
| `CSRF_TRUSTED_ORIGINS` | origens confiáveis | portas Vite | domínios HTTPS |
| `POSTGRES_URL` | URL de banco, maior prioridade | opcional | URL gerenciada possível |
| `DATABASE_URL` | URL de banco, segunda prioridade | opcional | URL gerenciada possível |
| `DATABASE_NAME/USER/PASSWORD/HOST/PORT` | conexão separada | PostgreSQL local | alternativa à URL |
| `EMAIL_BACKEND` | implementação de e-mail | SMTP padrão | backend do provedor |
| `EMAIL_HOST/PORT/USE_TLS` | servidor SMTP | Gmail:587/TLS por padrão | conforme provedor |
| `EMAIL_HOST_USER/PASSWORD` | credencial SMTP | segredo | segredo |
| `DEFAULT_FROM_EMAIL` | remetente | fallback user SMTP | remetente autorizado |
| `CELERY_BROKER_URL` | broker | `redis://127.0.0.1:6379/0` | URL Redis |
| `CELERY_RESULT_BACKEND` | resultados | fallback broker; ausente no example | URL Redis/opcional |
| `VITE_API_URL` | base Axios em build/runtime dev | localhost `/api` | URL pública backend `/api` |

`backend/.env.example` e `frontend/.env.example` são versionados; `.gitignore` exclui `.env` em qualquer nível e preserva examples. O workspace contém `.env` locais, mas seus valores não foram copiados. Variáveis Vite são incorporadas no bundle durante o build e não devem conter segredos.

## 12. Docker, containers e comunicação

### O que é

Imagem é o pacote imutável; container é uma instância. Compose descreve múltiplos serviços. Em uma rede Compose, DNS resolve pelo nome do serviço (`db`, `redis`); `localhost` dentro do container aponta ao próprio container.

### Neste projeto

| Serviço | Imagem/build e função | Portas | Volumes/dependências |
| --- | --- | --- | --- |
| `db` | `postgres:16-alpine` | 5432:5432 | `postgres_data`; healthcheck pg_isready |
| `redis` | `redis:7-alpine`, AOF | interna 6379 | `redis_data`; healthcheck ping |
| `backend` | Python 3.13 slim | 8000:8000 | bind `backend:/app`; aguarda db/redis saudáveis |
| `frontend` | Node 22 Alpine | 5173:5173 | bind frontend + volume node_modules; depende backend iniciado |
| `celery_worker` | mesma build backend | nenhuma | backend bind; db/redis/backend |
| `celery_beat` | mesma build backend | nenhuma | backend bind; db/redis/backend |

O backend instala apenas `requirements.txt`. O frontend usa `npm ci`. Compose sobrescreve host do banco para `db` e URLs Redis para `redis://redis:6379/0`. Já o navegador precisa chamar `http://localhost:8000/api`: ele está fora da rede Docker e não resolve `backend`. O PostgreSQL é publicado ao host; Redis não é.

Volumes nomeados persistem dados mesmo ao remover containers com `docker compose down`; `down -v` remove os volumes e apaga banco/Redis/node_modules. Redis usa AOF. Não há seção `networks`, então Compose cria uma rede padrão isolada do projeto.

Comandos reais:

```bash
docker compose --env-file backend/.env up --build
docker compose --env-file backend/.env up -d --build
docker compose ps
docker compose logs -f backend celery_worker celery_beat
docker compose exec backend python manage.py showmigrations
docker compose down
```

`DATABASE_PASSWORD` precisa ser não vazio antes da interpolação. O backend usa `runserver`, adequado ao desenvolvimento, não um servidor de produção.

## 13. Execução local sem Docker

Pré-requisitos não containerizados: Python compatível, Node/npm, PostgreSQL e Redis para lembretes. O repositório não fixa versões do host; Docker fixa Python 3.13 e Node 22.

```powershell
git clone https://github.com/orlandoconceicao/study-tracker.git
cd study-tracker

cd backend
Copy-Item .env.example .env
# preencher SECRET_KEY, DATABASE_* e opcionalmente SMTP/Redis
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Em terminais extras, dentro de `backend`:

```powershell
.\.venv\Scripts\celery.exe -A config worker -l info
.\.venv\Scripts\celery.exe -A config beat -l info
```

Frontend:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

PostgreSQL deve conter o banco/usuário do `.env`; Redis local deve ouvir em 127.0.0.1:6379. O frontend fica em 5173 e backend em 8000.

### Conteúdo educacional

Management commands comprovados:

```powershell
python manage.py seed_education
python manage.py import_curriculum_outline <arquivo>
python manage.py audit_education_content
python manage.py audit_education_content --unpublish-incomplete
python manage.py validate_education
```

`seed_education` usa dados JSON e `update_or_create`; a documentação interna recomenda slugs estáveis e auditoria antes de publicar. `content_quality.py` exige aula publicada, introdução/contexto/explicação/orientação/revisão, exemplos e exercícios com gabarito/explicação.

## 14. Dependências, scripts, testes e build

Backend: Django/DRF fornecem framework/API; SimpleJWT autenticação; django-filter filtros; cors-headers CORS; spectacular OpenAPI; psycopg PostgreSQL; dotenv `.env`; Celery/redis tarefas; dj-database-url URLs gerenciadas. Em desenvolvimento, pytest, pytest-django, pytest-cov e factory-boy.

Frontend scripts:

| Script | Finalidade |
| --- | --- |
| `npm run dev` | Vite com hot reload |
| `npm run build` | bundle de produção em `frontend/dist` |
| `npm run preview` | servir o bundle localmente |
| `npm test` | Vitest uma vez |
| `npm run test:watch` | modo observação |
| `npm run test:coverage` | cobertura V8, texto/HTML/LCOV |

Não há script lint nem ESLint configurado. O build usa `index.html` e `src/main.jsx`; Vite gera `dist`, ignorado pelo Git.

### Cobertura de testes encontrada

Backend tem testes duplicados entre arquivos legados por app e suíte `backend/tests`. Cobrem registro/login/refresh, payloads, isolamento, perfil/senha/preferências/desativação; Study model/serializer/CRUD/filtros/calendário/estatísticas/permissão; notificações, timezone, falha e deduplicação. Não foram encontrados testes para o grande app `education`.

Frontend possui testes para API client, studies service, AuthContext, login/cadastro, guarda de Layout, dashboard/recentes/calendário, páginas de estudos/formulário/estatísticas/configurações, tema e contraste. Não existe teste E2E navegador.

Comandos:

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
python -m pytest --cov

cd ../frontend
npm test
npm run test:coverage
npm run build
```

Nesta auditoria, o backend não executou porque o ambiente disponibilizava apenas o alias indisponível da Microsoft Store para Python. Vitest/build foram bloqueados pelo sandbox quando esbuild tentou ler diretórios ancestrais. Isso não comprova defeito do código. A validação Compose com `.env.example` recusou corretamente `DATABASE_PASSWORD` vazia.

## 15. Deploy e produção

### Evidência encontrada

O README aponta frontend e backend publicados em Vercel. A pasta local não versionada `.vercel/repo.json` vincula somente `backend/` ao projeto `study-tracker-backend`. Não há `vercel.json`, workflow, script de build/deploy, handler serverless explícito, ASGI, Gunicorn, configuração de frontend na Vercel ou configuração versionada do provedor de banco/Redis.

Portanto é possível afirmar que houve vínculo/deploy Vercel, mas **não reconstruir o deploy completo a partir do Git**. Não se deve inferir Neon/Supabase: o comentário em settings enumera possibilidades, não prova o provedor. `POSTGRES_URL`/`DATABASE_URL` com SSL é o único contrato comprovado para banco de produção.

### Frontend

Uma configuração plausível na plataforma seria root `frontend`, comando `npm run build`, output `dist` e `VITE_API_URL` apontando ao backend, mas esses valores **não estão versionados** e por isso não são confirmados. Como usa `BrowserRouter`, o host precisa reescrever rotas como `/settings` para `index.html`; nenhuma regra está no repo.

### Backend

O código expõe WSGI (`config.wsgi.application`) e requirements, mas não contém adaptação Vercel visível. Também não há comando de migration em pipeline. O Dockerfile usa Django `runserver`, não deve ser tomado como deploy robusto. Static tem somente `STATIC_URL="static/"`; não há `STATIC_ROOT`, WhiteNoise ou coleta configurada. O Admin e Swagger dependem de estáticos que a plataforma precisa servir.

### Banco, Redis, HTTPS e CORS

Produção por URL de banco força SSL. Pooling não está configurado e `conn_max_age=0` fecha/reabre conexões, coerente com serverless. O provedor não pode ser confirmado. Redis de produção também não pode; se tarefas Celery não estiverem hospedadas continuamente, lembretes não rodam apenas por publicar o Django na Vercel. HTTPS provavelmente termina na plataforma indicada, mas não há configuração que permita confirmar detalhes. `ALLOWED_HOSTS`, CORS e CSRF devem conter domínios reais via ambiente; nenhum domínio de produção está codificado.

Não há GitHub Actions/CI/CD no repositório. Deploy automatizado, triggers e migrations de produção não podem ser documentados como existentes.

## 16. Admin, OpenAPI, logs, estáticos e integrações

Admin está em `/admin/`. Registrados: User, Study, UserNotificationSettings e quase todo o domínio educacional (níveis, séries, matérias, vínculos, unidades, tópicos, aulas, exercícios/alternativas/tentativas, progressos, perfis, turmas/memberships/atividades, diagnósticos/respostas e assignments/respostas). `Curriculum`, `KnowledgeObject`, `Skill` e `Example` não aparecem registrados diretamente no `education/admin.py` atual.

OpenAPI: `/api/schema/` gera schema via drf-spectacular; `/api/docs/` serve Swagger UI, título “Study Tracker API”, versão 1.0.0.

Logs: não há dicionário `LOGGING`; usa configuração padrão Django/Celery. A task registra warning para timezone inválido e exception com stack trace para SMTP. Destinos/rotação não são customizados.

Estáticos: apenas `STATIC_URL`; não há media settings nem models com File/ImageField. Integração externa comprovada é SMTP. Não há APIs de terceiros.

Performance real: índices em datas/assunto/status/ordem e compostos; `select_related`, `prefetch_related`, `annotate`, `distinct`, bulk_create e paginação opcional em exercícios. Não há cache Redis: Redis é broker/result backend Celery.

## 17. Limitações e pontos de atenção

1. `ReviewViewSet`, `RecommendationViewSet` e `LegacyReviewViewSet` não são registrados em `education/urls.py`; portanto não são API pública.
2. `recommendation_service.py` e `review_services.py` ainda filtram campos `child`, removidos dos models pela migration `0013`; se chamados, tendem a gerar `FieldError`. `views.py` também referencia `Child` e `child_for_request` sem import/definição em caminhos não registrados.
3. `GET diagnostics/{id}/result/` está documentado em `docs/API.md`, mas não existe na classe roteada. O resultado só volta em `finish`; o método `result` está deslocado.
4. O frontend guarda refresh token, mas nunca o usa; qualquer 401 encerra a sessão.
5. O frontend não possui telas para educação/turmas/diagnósticos/assignments.
6. Não há testes do app education, apesar de ser o domínio mais complexo.
7. `AUTH_PASSWORD_VALIDATORS=[]`; a política efetiva é basicamente mínimo de oito caracteres nos serializers.
8. A fallback `unsafe-development-key` permite iniciar sem `SECRET_KEY`; é insegura em produção.
9. Deploy não é reproduzível pelo repositório; falta configuração versionada e procedimento de migrations/workers.
10. `runserver` aparece no Docker/Compose, adequado só para desenvolvimento.
11. Não há rate limit, blacklist de tokens, cache, monitoramento ou logging estruturado.
12. `ClassroomActivity.clean()` não é automaticamente chamado por `save()`, mas a API replica a validação no serializer; criações fora dele devem chamar `full_clean()`.
13. Question bank não filtra explicitamente status publicado no `get_queryset`; usuário autenticado pode listar exercícios em draft/review nessa rota.
14. `Exercise.reveal` permite revelar o gabarito sem registrar tentativa, por decisão expressa do endpoint.
15. Pasta `.vercel/` local está não rastreada e não consta no `.gitignore` atual, apesar do README interno da ferramenta recomendar não compartilhá-la.

## 18. Troubleshooting

| Sintoma | Causa provável / investigação |
| --- | --- |
| banco não conecta | confira serviço PostgreSQL, `DATABASE_*`; dentro do Docker host é `db`, fora é 127.0.0.1 |
| Compose reclama de senha | copie example e defina `DATABASE_PASSWORD`; a interpolação usa `:?` |
| Redis/Celery não conecta | fora use 127.0.0.1; dentro use `redis`; confira `docker compose ps/logs` |
| lembrete não chega | valide enabled/hora/fuso/e-mail, SMTP, worker e beat; veja logs do worker |
| CORS no navegador | origem exata (scheme/host/porta) precisa estar em `CORS_ALLOWED_ORIGINS` |
| 401 | access ausente/expirado/inválido; frontend não renova automaticamente |
| 403 | autenticado, mas sem staff/papel professor/ownership/membership exigido |
| 404 de ID existente | queryset pode ocultar recurso de outro usuário; confira ownership |
| Swagger/Admin sem estilo | deploy não possui estratégia de staticfiles confirmada |
| rota React retorna 404 ao atualizar | host precisa fallback de SPA para `index.html` |
| migration pendente | `showmigrations`, `makemigrations --check --dry-run`, depois `migrate` |
| diagnóstico recusa iniciar | tópico precisa de ao menos cinco exercícios com alternativa correta |
| review/recommendation gera erro | código legado usa `child` removido e não está roteado |

## 19. Git e comandos úteis

Remote configurado: `origin` em `https://github.com/orlandoconceicao/study-tracker.git`; branch atual/principal observada: `main`, sincronizada com `origin/main` no início da auditoria. O fluxo de equipe não está documentado. `.gitignore` protege segredos, ambientes, banco SQLite, mídia/estáticos gerados, Celery beat, caches, cobertura, node_modules e dist.

```powershell
git status
git diff -- ESTUDO_DO_PROJETO.md

# Django
python manage.py shell
python manage.py dbshell
python manage.py showmigrations
python manage.py createsuperuser

# Docker
docker compose ps
docker compose logs -f
docker compose exec backend python manage.py shell
docker compose exec db psql -U <usuario> -d <banco>
```

## 20. Glossário

- **API REST**: interface HTTP de recursos JSON; neste projeto, DRF sob `/api`.
- **Serializer**: contrato/validação entre JSON e models.
- **ORM**: camada Django que traduz consultas Python para SQL.
- **Migration**: versão executável da estrutura/dados do banco.
- **JWT**: token assinado usado no header Bearer.
- **CORS**: regra que autoriza o frontend de outra origem a chamar a API.
- **CSRF**: proteção contra requisição forjada; mais relevante a autenticação por cookie, mas middleware/origens existem.
- **WSGI**: interface síncrona que expõe a aplicação Django.
- **Celery**: executor de tarefas fora da request web.
- **Broker**: fila intermediária; aqui, Redis.
- **Beat**: scheduler periódico do Celery.
- **Container**: processo isolado criado de uma imagem.
- **Volume**: armazenamento persistente gerenciado pelo Docker.
- **ViewSet/router**: conjunto DRF de ações e gerador de URLs REST.
- **Ownership**: autorização baseada no dono do registro.

## 21. Mapa final do sistema

```text
USUÁRIO
  └─► React/Vite (estado local + AuthContext)
        ├─► localStorage: access + refresh + preferência de tema
        └─► Axios (VITE_API_URL, Bearer access)
              └─► config/urls.py
                    ├─► users → conta/preferences → User/UserPreferences
                    ├─► studies → serializer/filter/services → Study
                    ├─► notifications → settings/test → SMTP
                    └─► education
                          ├─► currículo publicado / escrita staff
                          ├─► tentativa/progresso/diagnóstico
                          └─► professor → turma → aluno → assignment
                                │
                                ▼
                           Django ORM
                                │
                                ▼
                           PostgreSQL

Celery Beat ─► Redis ─► Celery Worker ─► SMTP

Docker Compose: db + redis + backend + frontend + worker + beat
Deploy observado: links/Vercel, porém configuração completa não versionada
```

## 22. Referências auditadas

Principais arquivos: `README.md`, `docs/API.md`, `docs/EDUCATION_CONTENT.md`, `.gitignore`, `docker-compose.yml`; todo `backend/config`; requirements/Dockerfile/examples de ambiente; models, serializers, views, URLs, permissions, services, tasks, admin, migrations, tests e management commands dos quatro apps; `frontend/package.json`, Vite/Docker/env, `src/main.jsx`, `App.jsx`, context, hook, services, páginas, componentes, estilos e testes.

Partes não encontradas ou impossíveis de confirmar: provedor real do banco e Redis de produção, pooling externo, configuração reproduzível Vercel, comando de deploy/migrations, servidor produtivo, CI/CD, terminação HTTPS detalhada, monitoramento, rate limiting, cache, Channels/WebSockets, mídia e cobertura percentual atual.

Nenhum dado inventado: **confirmado**. Suposições de configuração não confirmadas foram identificadas como tais.
