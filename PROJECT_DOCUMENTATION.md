# Guia Completo de Estudo do Projeto

> Auditoria técnica e didática do código existente no workspace em 23/08/2026. As afirmações abaixo vêm dos arquivos do repositório; quando não há evidência, isso é indicado explicitamente. Valores secretos não são reproduzidos.

## Como usar este material

Esta apostila foi organizada para duas leituras. Na primeira, siga a ordem: visão geral, arquitetura, frontend, backend, banco e infraestrutura. Assim você acompanha o caminho que uma ação percorre desde o navegador até o PostgreSQL. Na segunda, use os caminhos de arquivos como roteiro: abra o código citado, localize a função e compare cada explicação com a implementação.

Ao encontrar os blocos **O que é**, aprenda o conceito geral. Nos blocos **Neste projeto**, veja a aplicação concreta. Os fluxos em texto mostram o que acontece antes e depois de cada etapa. Ao final há exercícios sem mudanças destrutivas, perguntas de revisão e um gabarito separado.

Conhecimento prévio útil: variáveis, funções, condições, arrays, objetos e noções de HTML/CSS. Não é necessário dominar React ou Django antes de começar.

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
│   │   ├── pages/       # estudos, formulário, estatísticas, configurações e 404
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

### Perguntas para revisar: backend e banco

1. Qual é a responsabilidade diferente de URL, view, serializer, service e model?
2. Por que `StudyViewSet` filtra o queryset e também usa uma permission de objeto?
3. O que `transaction.atomic` protege nos fluxos educacionais?
4. Como ForeignKey, OneToOne e ManyToMany aparecem neste banco?
5. Por que uma migration deve ser versionada junto da alteração de model?
6. O que impede um usuário de consultar estudos de outro usuário?

## 7. API e roteamento

Todas as rotas abaixo começam em `backend/config/urls.py`. Salvo registro, login e refresh, a permissão global exige JWT.

### O que são API, HTTP e JSON

API é o contrato pelo qual frontend e backend conversam. HTTP transporta a mensagem: método, URL, headers e eventualmente body. JSON é o formato de dados usado aqui. `GET` consulta; `POST` cria ou dispara ação; `PUT` substitui; `PATCH` altera parcialmente; `DELETE` remove/desativa. O header `Authorization: Bearer ...` leva a identidade. Status 2xx indica sucesso, 400 entrada inválida, 401 falta de autenticação válida, 403 falta de autorização, 404 recurso não visível/encontrado e 5xx falha do servidor.

Pense numa request como uma pergunta completa, não apenas uma URL:

```text
PATCH /api/studies/7/
Authorization: Bearer <access>
Content-Type: application/json

{"duration_minutes": 90}
```

Axios constrói essa mensagem; Django resolve a rota; JWT identifica o usuário; serializer valida o body; view encontra o objeto permitido; ORM produz SQL; DRF devolve status e JSON.

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

O frontend é a parte executada pelo navegador. Ele não acessa o PostgreSQL diretamente: renderiza HTML por meio do React, reage aos eventos do usuário e troca JSON com a API Django. Os arquivos desta camada estão em `frontend/`.

### 9.1 Do HTML até o primeiro componente

#### `frontend/index.html`

**O que é:** HTML fornece a estrutura inicial que o navegador entende sem precisar do React. Neste projeto o arquivo é deliberadamente pequeno porque a interface será construída por JavaScript.

Trecho real, apenas formatado para leitura:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>Study Tracker</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

Leitura passo a passo:

1. `<!doctype html>` seleciona o padrão HTML moderno.
2. `lang="pt-BR"` informa idioma a navegador, leitor de tela e mecanismos de busca.
3. `charset="UTF-8"` permite acentos e símbolos.
4. `viewport` faz a largura lógica acompanhar o dispositivo; sem ele, o layout mobile seria reduzido como uma página desktop.
5. `favicon.svg`, em `frontend/public/favicon.svg`, é servido na raiz pelo Vite.
6. `<title>` define o texto da aba. Não há description, Open Graph ou outras configurações SEO encontradas.
7. `#root` começa vazio e funciona como ponto de montagem.
8. `type="module"` habilita imports ES Modules e executa `src/main.jsx`.

```text
index.html → #root vazio → main.jsx encontra #root → React monta a interface
```

#### `frontend/src/main.jsx`

**Por que existe:** centraliza a inicialização. Ele não descreve uma página específica; prepara serviços globais dos quais toda a árvore depende.

```jsx
initializeTheme();
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider><App /></AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
```

`initializeTheme()` aplica a preferência antes da montagem, reduzindo troca visual de cores. `document.getElementById` é DOM nativo; `createRoot` entrega esse nó ao React. `StrictMode` adiciona verificações no desenvolvimento e pode executar certos ciclos duas vezes para revelar efeitos inseguros; não cria elemento visual. `BrowserRouter` disponibiliza navegação por URL. `AuthProvider` disponibiliza sessão e preferências. Por composição, `App` fica dentro de todos esses recursos.

**Conceitos para aprender:** DOM, ponto de entrada, árvore de componentes, composição e providers.

#### `frontend/src/App.jsx`

**O que é:** é o mapa entre URL e tela. Ser “principal” aqui significa decidir qual ramo da árvore renderizar, não concentrar toda a lógica.

`Routes` procura uma `Route` compatível. Login e cadastro ficam fora do layout protegido. A raiz `/` usa `<Navigate replace>` para levar a entrada do site à dashboard sem manter a URL intermediária no histórico. A route sem `path`, com `element={<Layout />}`, é uma rota-pai: suas filhas aparecem no `<Outlet>` do Layout. O curinga `*` renderiza `NotFound`; assim uma URL realmente inexistente não é confundida com uma página válida.

```text
main.jsx
  ↓
App.jsx escolhe a rota
  ├─ / → Navigate → /dashboard
  ├─ /login → LoginPage
  ├─ /register → RegisterPage
  ├─ rota privada → Layout → Outlet → página escolhida
  └─ caminho inexistente → NotFound → link para /dashboard
```

### 9.2 Fundamentos de JavaScript e React vistos no código

#### Componentes e JSX

Um componente React é uma função que devolve JSX. JSX se parece com HTML, mas é sintaxe JavaScript transformada pelo Vite. `StatCard({ label, value, detail, accent })`, em `frontend/src/components/dashboard/StatCard.jsx`, recebe dados e devolve um `<article>`.

#### Props

Props são entradas enviadas pelo pai. `DashboardHome` envia `label`, `value` e `accent` para `StatCard`; o filho apenas apresenta esses valores. Isso separa **qual dado mostrar** (pai) de **como mostrar** (filho).

```text
DashboardHome (pai) → props → StatCard (filho) → JSX
```

Outros exemplos: `RecentStudies` recebe `studies` e `loading`; `Sidebar` recebe callbacks `onLogout` e `onNavigate`; `AuthInput` recebe label, type e demais atributos. Props não devem ser alteradas diretamente pelo filho.

#### Estado com `useState`

Estado é memória que pertence à instância renderizada do componente. Em `frontend/src/components/Calendar.jsx`:

```jsx
const [current, setCurrent] = useState(new Date());
const [data, setData] = useState({});
const [error, setError] = useState("");
```

`current` é o valor atual, `setCurrent` solicita uma atualização e `new Date()` é o inicial. Ao chamar o setter, React agenda nova renderização; variáveis locais comuns seriam recriadas e não notificariam o React. Calendar precisa disso porque mês, dados e erro mudam enquanto a tela existe.

#### Efeitos com `useEffect`

Efeito sincroniza o componente com algo externo: rede, DOM, eventos ou mídia do sistema.

- `useEffect(..., [])` em `AuthContext` carrega a sessão uma vez após a montagem e registra `study-session-expired`. O retorno remove o listener no unmount: esse retorno é o **cleanup**.
- `useEffect(..., [month, year])` em Calendar refaz a consulta sempre que mês ou ano mudam.
- `useEffect(..., [preferences.theme])` aplica o tema e substitui o listener de `matchMedia` quando a preferência muda.
- `useEffect(..., [id])` em StudyForm carrega um registro quando a rota de edição fornece outro ID.

O array de dependências responde “quais valores usados pelo efeito fazem necessário executá-lo novamente?”. Array vazio significa nenhuma dependência variável; omitir o array faria rodar após toda renderização.

#### Outros hooks

`useContext` lê o contexto; `useAuth`, em `frontend/src/hooks/useAuth.js`, encapsula essa leitura. `useNavigate` devolve uma função para navegação programática após login/salvamento. `useParams` lê `:id` da URL. `useLocation` permite fechar o drawer quando o caminho muda. `useCallback` em Studies preserva a função `load` entre renders enquanto seus filtros não mudam. `useMemo` em Settings memoriza o rótulo da conta a partir de `user`; neste caso é uma otimização pequena, não estado.

#### Arrow functions, desestruturação e spread

`const submit = async (event) => { ... }` é arrow function armazenada numa constante. Diferentemente de `function submit() {}`, ela não cria seu próprio `this`; o projeto não depende de `this` nos componentes funcionais.

Em `const { user, logout, loading } = useAuth()`, desestruturação retira propriedades do objeto. Em `setForm({ ...form, subject: event.target.value })`, spread copia as propriedades atuais e a última propriedade substitui apenas `subject`. Sem a cópia, os demais campos seriam perdidos.

#### `map`, condições e chaves

`studies.map((study) => <article key={study.id}>...)` transforma cada objeto em elemento. `key` ajuda React a reconhecer qual item permaneceu, entrou ou saiu. Condições aparecem como `error && <p>...` (renderiza somente se truthy) e `loading ? A : B` (escolhe um dos ramos).

### 9.3 Context API e autenticação no frontend

**Arquivo:** `frontend/src/context/AuthContext.jsx`

**Consumidor:** `frontend/src/hooks/useAuth.js`

Context evita passar `user`, `login` e `logout` por props em todas as camadas. `createContext(null)` cria o canal; `AuthProvider` mantém estado e entrega um `value`; `useAuth` permite que Layout, Dashboard, AuthPages e Settings consumam esse valor.

```text
AuthProvider
  ├─ estado: user, preferences, loading
  ├─ ações: login, logout, register, updateProfile, updatePreferences
  └─ qualquer descendente → useAuth() → mesmo estado compartilhado
```

No primeiro carregamento, o provider procura access token. Se existir, busca perfil e preferências em paralelo. `finally` encerra o loading até em falha. No login, primeiro recebe tokens, depois consulta os dados e só então a página navega. Essa ordem impede a dashboard de abrir sem usuário carregado.

### 9.4 Componentes importantes como casos de estudo

#### `Layout`

**Arquivo:** `frontend/src/components/Layout.jsx`

**O que é e por que existe:** casca reutilizada pelas telas privadas. Centraliza sidebar, área de conteúdo, menu mobile e guarda de autenticação, evitando repetição em cada página.

**Entradas:** nenhuma prop; lê contexto e localização.

**Estado:** `open`, inicialmente falso, decide a classe do drawer.

**Eventos:** botão alterna `open`; logout chama contexto; mudança de rota fecha drawer.

**Filhos:** duas instâncias visuais de Sidebar e `Outlet`.

**Fluxo:** loading → mensagem; sem user → login; com user → shell privado.

**O que aprender:** layout aninhado, guarda de rota, renderização condicional e responsabilidade compartilhada sem duplicar páginas.

#### `DashboardHome`

**Arquivo:** `frontend/src/components/dashboard/DashboardHome.jsx`

Na montagem, `Promise.all` dispara estatísticas e listagem simultaneamente. Depois grava `stats` e os cinco primeiros estudos. `greeting()` e `hours()` são funções puras: recebem/leem dados e calculam texto sem alterar estado externo. A página compõe `StatCard`, `Calendar` e `RecentStudies`; isso demonstra decomposição de uma tela complexa.

#### `Calendar`

**Arquivo:** `frontend/src/components/Calendar.jsx`

Além do efeito mensal, `openDay` é assíncrona: só consulta detalhes se o resumo indicar estudo. `Array.from` cria espaços antes do primeiro dia e botões para todos os dias. `padStart` forma datas `YYYY-MM-DD`. Botões com `aria-label` tornam setas compreensíveis a leitores de tela.

#### `Studies` e `StudyForm`

**Arquivos:** `frontend/src/pages/studies.jsx`, `frontend/src/pages/study-form.jsx`

Studies usa formulário de filtros e mantém `items`, `filters`, loading, erro e ID em exclusão. O submit chama `preventDefault()` para evitar recarregar o documento. A exclusão pede confirmação, chama DELETE e recarrega a lista.

StudyForm reutiliza a mesma tela para criar e editar. A presença de `id` muda título, carregamento e método (`POST` ou `PATCH`). Inputs controlados recebem `value` do estado e `onChange` escreve de volta. No submit, minutos viram Number; após sucesso, `navigate('/dashboard')`.

```text
digitação → onChange → setForm → render → value atualizado
submit → preventDefault → API → sucesso/erro → navegação/mensagem
```

#### `Settings`

**Arquivo:** `frontend/src/pages/settings.jsx`

É o formulário mais complexo. Separa estados “editado” e “salvo” para habilitar botões apenas quando há mudança. `submit(key, action, success)` é uma função de ordem superior: recebe outra função (`action`) e reutiliza loading/status/try-catch-finally em perfil, senha, lembrete e preferências. `message()` normaliza formatos de erro do DRF. A conta usa `DELETE` com body e depois limpa a sessão.

#### Componentes menores

- `AuthPages.jsx`: contém LoginPage/RegisterPage e o wrapper Shell; coordena estado de formulário e contexto.
- `not-found.jsx`: fallback público simples; identifica o erro 404 e oferece um `Link` válido para a dashboard, que por sua vez passa pela guarda de autenticação.
- `AuthInput.jsx`: propaga atributos com `{...props}`, controla visibilidade de senha e expõe `aria-invalid`.
- `AuthLayout.jsx`: estrutura visual das telas públicas.
- `Sidebar.jsx`: mapeia configuração de links em `NavLink`; a classe `active` depende da rota.
- `RecentStudies.jsx`: formata duração, mapeia itens e oferece empty state.
- `StatCard.jsx`: componente puramente apresentacional.

### 9.5 Eventos, formulários e acessibilidade

Eventos React são props em camelCase. `onClick` navega, abre menu ou exclui; `onChange` sincroniza inputs; `onSubmit` valida/envia. Não há `onMouseEnter` no código. Usar `<button>` para ações e `<Link>` para navegação preserva semântica de teclado melhor do que uma `<div onClick>`.

O projeto usa `label` envolvendo inputs ou `htmlFor/id`, `required`, tipos email/password/date/number, limites min/max, `aria-label`, `aria-expanded`, `aria-hidden`, `aria-invalid` e `role="status"`. Não há imagens de conteúdo com `alt`: os recursos visuais de autenticação são CSS/HTML e o único asset é favicon SVG. O HTML semântico inclui `main`, `aside`, `nav`, `header`, `section`, `article`, `footer` e `dl`.

### 9.6 CSS real, tema e responsividade

**Arquivos:** `frontend/src/styles/global.css` e `frontend/src/styles/auth.css`.

`global.css` é importado no entry point e afeta toda a aplicação; `auth.css` é carregado por AuthPages e especializa login/cadastro. Não há CSS Modules, Tailwind ou biblioteca de componentes.

#### Variáveis CSS e tema

`:root` declara tokens como `--color-background`, `--color-surface`, `--color-primary`, `--color-text` e `--color-border`. Componentes usam `var(--color-text)` em vez de repetir hexadecimal. `:root[data-theme="dark"]` redefine os mesmos nomes; a estrutura não muda, apenas os valores resolvidos.

`services/theme.js` lê `study_theme` do localStorage, aceita light/dark/system, consulta `matchMedia('(prefers-color-scheme: dark)')`, define `document.documentElement.dataset.theme` e `style.colorScheme`. `localStorage` é armazenamento chave/valor persistente do navegador; permanece após fechar a aba, mas é acessível ao JavaScript da mesma origem.

```text
preferência salva/servidor → applyTheme
→ data-theme no <html> → conjunto de variáveis muda → todos os seletores recolorem
```

Não há botão exclusivo de tema no header; a escolha é um `<select>` em Settings e também é persistida no backend como preferência.

#### Flexbox

Flexbox organiza itens em uma dimensão. `display:flex` ativa o contexto; `justify-content` distribui no eixo principal; `align-items` alinha no eixo transversal; `gap` separa sem margens individuais. Exemplos reais: `.app-shell` coloca sidebar e workspace; `.dashboard-hero` separa título e botão; `.study-record` alinha marca, conteúdo e ações; `.settings-actions` envia botões ao fim.

#### Grid

Grid organiza linhas e colunas. `grid-template-columns` define a malha e `gap` os intervalos. `.filter-fields` cria três colunas flexíveis e uma para o botão; `.settings-grid` cria duas colunas; `.study-form-fields` duas; `.progress-metrics` três. `minmax(0, 1fr)` permite encolher conteúdo sem estourar a coluna.

#### Responsividade

A folha é predominantemente desktop-first: define múltiplas colunas/sidebar fixa e depois reduz com `@media (max-width: ...)`. Há breakpoints em `global.css` e `auth.css`, incluindo 1100, 980, 900, 760, 680 e 400 px. Em telas menores, grades passam a uma coluna, a sidebar desktop some, o botão mobile/drawer aparece, hero empilha e ações/formulários ocupam melhor a largura. Em AuthLayout, duas colunas viram uma e a área decorativa é ocultada/reorganizada nos menores tamanhos.

```text
desktop: sidebar | workspace       login: marca | formulário
mobile:  botão + drawer / conteúdo login: formulário em uma coluna
```

### 9.7 Imports, exports e módulos

Cada arquivo ES Module controla seu escopo. `export default api` permite qualquer nome no import (`import api from ...`). `export const studiesApi` é export nomeado e deve ser importado entre chaves. Imports relativos como `../services/studies` percorrem pastas; dependências como `react` são resolvidas de `node_modules`. O package define `"type":"module"`, portanto configurações `.js` também usam `import/export`.

### 9.8 O que acontece quando você abre o site

1. O navegador solicita o domínio. A forma exata como a Vercel/CDN entrega os arquivos não está versionada.
2. Recebe `index.html`, encontra metadados, favicon, `#root` e script.
3. Baixa o bundle JavaScript/CSS (em dev, módulos servidos pelo Vite).
4. `main.jsx` inicializa tema e monta React.
5. BrowserRouter lê a URL; AuthProvider tenta restaurar a sessão.
6. App escolhe a rota. `/` redireciona à dashboard, uma rota desconhecida mostra `NotFound` e, se a rota escolhida for privada, Layout aguarda `loading`.
7. Com token válido, Axios busca usuário/preferências e a página é renderizada; sem usuário, Layout redireciona.
8. CSS aplica layout, tokens e breakpoint.
9. Effects da página carregam seus dados; setters causam novas renderizações.
10. Eventos ficam prontos para clique, digitação e submit.

### Perguntas para revisar: frontend

1. Por que `#root` começa vazio?
2. Qual é a diferença entre props e state usando StatCard e Calendar como exemplos?
3. Por que Calendar declara `[month, year]` nas dependências do efeito?
4. Como Layout protege as rotas sem repetir lógica em cada página?
5. O que muda no CSS quando `data-theme="dark"` é aplicado?
6. Qual a diferença entre `Link`, `NavLink`, `Navigate` e `useNavigate` neste projeto?
7. Por que inputs do StudyForm são chamados de controlados?
8. Onde o projeto usa Grid e onde usa Flexbox?

### Inicialização, rotas e estado

`src/main.jsx` inicializa tema, monta `createRoot`, `BrowserRouter`, `AuthProvider` e `App` sob StrictMode:

```text
main.jsx → BrowserRouter → AuthProvider → App → Routes
                                      └→ Layout → Sidebar + Outlet → Page
```

| Rota | Componente | Acesso/dados |
| --- | --- | --- |
| `/` | `Navigate` | redirecionamento explícito e substitutivo para `/dashboard` |
| `/login` | `LoginPage` | pública; login JWT |
| `/register` | `RegisterPage` | pública; cadastro |
| `/dashboard` | `DashboardHome` | Layout protegido; estatísticas, estudos e calendário |
| `/studies` | `Studies` | lista/filtros/exclusão |
| `/studies/new` | `StudyForm` | criação |
| `/studies/:id/edit` | `StudyForm` | detalhe + patch |
| `/statistics` | `Statistics` | agregados |
| `/settings` | `Settings` | perfil, preferências, lembrete, senha e conta |
| `*` (qualquer outra) | `NotFound` | fallback público 404; informa que a URL não existe e oferece retorno à dashboard |

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

#### Dockerfiles, instrução por instrução

`backend/Dockerfile` começa com `FROM python:3.13-slim`: a nova imagem herda Python e um sistema enxuto. `ENV PYTHONDONTWRITEBYTECODE=1` evita `.pyc`; `PYTHONUNBUFFERED=1` envia logs imediatamente. `WORKDIR /app` define o diretório dos próximos passos. `COPY requirements.txt ./` copia primeiro só as dependências, permitindo reutilizar cache quando o código muda. `RUN pip install --no-cache-dir -r requirements.txt` instala pacotes. Depois `COPY . .` leva o backend. `EXPOSE 8000` documenta a porta e `CMD` define `runserver` como processo padrão.

`frontend/Dockerfile` repete o padrão com `node:22-alpine`. Copia `package.json` e lock antes, executa `npm ci` para instalação reproduzível, copia o código, expõe 5173 e inicia Vite com `--host 0.0.0.0`, necessário para aceitar conexões vindas de fora do container.

Importante: `EXPOSE` não publica porta no computador. A publicação ocorre em `ports` do Compose, por exemplo `"8000:8000"` significa `porta do host:porta do container`.

#### Compose como orquestrador

Um Dockerfile descreve uma imagem; `docker-compose.yml` descreve o conjunto funcionando. `build` escolhe o Dockerfile, `image` usa imagem pronta, `environment/env_file` injeta configuração, `command` substitui o CMD, `depends_on` ordena inicialização conforme healthcheck, `volumes` persiste/monta arquivos e `ports` publica serviços.

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

### Perguntas para revisar: Docker

1. Qual a diferença entre imagem, container e serviço Compose?
2. Por que o backend usa `db:5432` dentro do Compose e o host usa `localhost:5432`?
3. Qual dado permanece em `postgres_data`?
4. Por que `COPY requirements.txt` ocorre antes de `COPY . .`?
5. O que muda entre `EXPOSE 8000` e `ports: 8000:8000`?

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

### Como ler `frontend/package.json`

`name` identifica o pacote, `private:true` evita publicação acidental no npm, `version` é 1.0.0 e `type:module` ativa ES Modules. `scripts` são atalhos executados pelo npm. `dependencies` precisam existir em execução: React/ReactDOM constroem a UI, React Router seleciona telas e Axios chama HTTP. `devDependencies` sustentam desenvolvimento/build/teste: Vite, plugin React, Vitest, jsdom, Testing Library e cobertura V8. O grande `package-lock.json` fixa a árvore exata, inclusive dependências transitivas; normalmente não é documentação para leitura linha por linha.

### Vite neste projeto

Vite é servidor de desenvolvimento e ferramenta de build. Em `npm run dev`, serve módulos rapidamente na porta padrão 5173 e aplica HMR: substitui módulos alterados sem recarregar tudo. `frontend/vite.config.js` habilita transformação React e configura Vitest/jsdom/cobertura. Variáveis públicas são lidas por `import.meta.env`; só `VITE_API_URL` aparece. No build, Vite resolve imports, transforma JSX, agrupa/minifica assets e grava `dist`. Não há etapa TypeScript porque o projeto usa JavaScript/JSX.

### Como os testes são estruturados

Vitest fornece `describe`, `test/it`, mocks e assertions. Testing Library consulta a interface como o usuário e jsdom simula DOM sem navegador real. `src/test/setup.js` limpa tela, localStorage e mocks após cada teste; `render.jsx` fornece Router e contexto padrão. No backend, pytest-django cria banco de teste conforme `settings_test.py`; fixtures de `backend/tests/conftest.py` preparam usuários e APIClient. Um teste unitário isola regra; um teste de integração cruza HTTP/ORM/framework. Não há números atuais de cobertura confirmados.

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

Frontend possui testes para API client, studies service, AuthContext, login/cadastro, guarda de Layout, dashboard/recentes/calendário, páginas de estudos/formulário/estatísticas/configurações, fallback 404, tema e contraste. `not-found.test.jsx` verifica o título acessível e se o link de retorno aponta para `/dashboard`. Não existe teste E2E em navegador real.

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

Na validação atual, `python -m pytest` foi executado pelo ambiente virtual existente e aprovou **53 testes backend**; `npm test` aprovou **41 testes em 15 arquivos frontend**. O frontend emite apenas avisos das future flags do React Router 7, não falhas. `npm run build` também concluiu, transformou 104 módulos e gerou `dist`. A validação Compose com `.env.example` recusou corretamente `DATABASE_PASSWORD` vazia.

## 15. Deploy e produção

### Desenvolvimento versus produção

Em desenvolvimento, Vite serve módulos com HMR em localhost:5173, Django `runserver` atende localhost:8000, configuração vem de `.env` local e banco/Redis podem estar no computador ou Compose. Em produção, o frontend deve ser um bundle `dist` otimizado servido por plataforma/CDN; a API usa domínio/HTTPS, DEBUG falso, secrets da plataforma e banco remoto. O código confirma os contratos de ambiente, mas não registra todos os passos de produção.

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
| URL React inexistente mostra “Página não encontrada” | comportamento esperado do `*`; use o link para a dashboard ou corrija a URL de origem |
| migration pendente | `showmigrations`, `makemigrations --check --dry-run`, depois `migrate` |
| diagnóstico recusa iniciar | tópico precisa de ao menos cinco exercícios com alternativa correta |
| review/recommendation gera erro | código legado usa `child` removido e não está roteado |

## 19. Git e comandos úteis

Remote configurado: `origin` em `https://github.com/orlandoconceicao/study-tracker.git`; branch atual/principal observada: `main`, sincronizada com `origin/main` no início da auditoria. O fluxo de equipe não está documentado. `.gitignore` protege segredos, ambientes, banco SQLite, mídia/estáticos gerados, Celery beat, caches, cobertura, node_modules e dist.

Git mantém versões. `git status` mostra mudanças; `git add <arquivo>` escolhe o conteúdo do próximo snapshot; `git commit -m "..."` grava localmente; `git push origin main` envia commits ao remoto. Push não é sinônimo comprovado de deploy: embora plataformas como Vercel frequentemente observem GitHub e executem install/build/deploy, os triggers deste projeto não estão versionados e não podem ser confirmados.

O `.gitignore` não apaga arquivos: apenas orienta o Git a não rastreá-los. `node_modules` pode ser reconstruído pelo lock; `.venv` pelas requirements; `dist` pelo build; `.env` deve ficar fora porque contém configuração/segredos locais.

```powershell
git status
git diff -- PROJECT_DOCUMENTATION.md

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

# Como construir este projeto do zero

> Esta trilha reconstrói a arquitetura que existe hoje. A ordem abaixo é uma sequência pedagógica realista, não um registro histórico dos commits originais — não foi possível confirmar a ordem histórica pelos arquivos atuais do projeto.

## Antes de começar: como pensar em incrementos

Não tente criar React, autenticação, currículo, Celery, Docker e deploy ao mesmo tempo. Quando cinco partes mudam juntas, um erro pode estar em qualquer uma delas. Trabalhe sempre neste ciclo:

```text
escolher um comportamento pequeno
→ criar a menor implementação útil
→ executar
→ testar o caminho feliz e um erro
→ salvar uma versão no Git
→ avançar
```

A estratégia será construir primeiro uma **fatia vertical** simples — model Study, endpoint e tela — e só depois aumentar os domínios. Assim confirmamos cedo que navegador, API e banco conseguem conversar.

### Mapa de arquivos e resultado esperado por etapa

| Etapa | Arquivos envolvidos | Resultado esperado |
| --- | --- | --- |
| 1 | raiz, `.gitignore`, `README.md`, `.env.example` | repositório limpo e arquitetura desenhada |
| 2 | `backend/manage.py`, `backend/config/*`, pastas dos apps | Django inicia e passa em `check` |
| 3 | `users/models.py`, settings e migrations | usuário customizado e PostgreSQL migrados |
| 4 | `studies/models.py`, serializer, view, URLs, services e testes | CRUD isolado por usuário |
| 5 | `users/serializers.py`, views/URLs e REST/JWT settings | cadastro, login e rota privada funcionando |
| 6 | `frontend/index.html`, `src/main.jsx`, `App.jsx`, Layout/pages | navegação React e guarda de rota |
| 7 | `styles/*.css`, `services/theme.js`, Settings | interface responsiva em claro/escuro/system |
| 8 | `services/api.js`, `studies.js`, AuthContext e páginas | primeira fatia ponta a ponta |
| 9 | services/actions de studies, Calendar/Statistics/preferences | dashboard e configurações com dados reais |
| 10 | notifications, `config/celery.py` e settings | lembrete único por dia via worker |
| 11 | models/serializers/views/services education, seeds e Admin | currículo e fluxos escolares autorizados |
| 12 | dois Dockerfiles e `docker-compose.yml` | seis serviços integrados e dados persistentes |
| 13 | testes, Vite build e configuração de produção | versão verificável e artefato `dist` |
| 14 | Git e configuração da plataforma escolhida | versão rastreável publicada e testada |

Em cada etapa, o **checkpoint** é o critério para avançar. Se ele falhar, não acumule outra camada por cima: reproduza, isole e corrija primeiro.

## Etapa 1. Planejar domínio, repositório e ferramentas

### Objetivo

Transformar a ideia “acompanhar estudos” em entidades e entregas pequenas antes de escrever código.

### Por que começamos por aqui

Framework não decide quais dados o produto precisa. Primeiro perguntaríamos: quem usa? O que registra? O que precisa consultar? Neste projeto, a primeira fatia pede User e Study. Preferências, lembretes e educação podem vir depois.

### Decisões iniciais coerentes com o projeto

- Monorepo com `backend/` e `frontend/`: um repositório, duas aplicações separadas.
- Django/DRF para modelagem e API; React/Vite para cliente; PostgreSQL para persistência.
- JavaScript/JSX, não TypeScript. Não configure TypeScript numa reconstrução fiel.
- HTTP/JSON entre aplicações; autenticação JWT.

### Passo a passo

```bash
mkdir study-tracker
cd study-tracker
git init
mkdir backend frontend docs
```

Criaríamos desde cedo `.gitignore`, `README.md` curto e `.env.example` sem valores secretos. O `.gitignore` real serve como modelo para Python, Node, ambientes, cobertura, `.env` e builds.

### Como saber se deu certo

`git status` deve mostrar apenas os arquivos iniciais que você pretende versionar, nunca `.env`, `.venv` ou `node_modules`.

### Checkpoint

Antes de continuar, você deve conseguir explicar por que frontend e backend são processos separados e desenhar `navegador → API → banco`.

### O que aprendemos

Arquitetura começa pelas responsabilidades e pelo fluxo dos dados, não pela escolha de nomes de arquivos.

## Etapa 2. Criar a base Django

### Objetivo

Ter um servidor Django vazio funcionando e preparado para receber apps.

### O que vamos criar

Ambiente Python, dependências, projeto `config` e os quatro apps existentes.

### Passo a passo

No diretório `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "Django>=5.1,<6.0" `
  "djangorestframework>=3.15,<4.0" `
  "djangorestframework-simplejwt>=5.3,<6.0" `
  "django-filter>=24.3,<26.0" `
  "django-cors-headers>=4.4,<5.0" `
  "drf-spectacular>=0.27,<1.0" `
  "psycopg[binary]>=3.2,<4.0" `
  "python-dotenv>=1.0,<2.0"
.\.venv\Scripts\django-admin.exe startproject config .
.\.venv\Scripts\python.exe manage.py startapp users
.\.venv\Scripts\python.exe manage.py startapp studies
.\.venv\Scripts\python.exe manage.py startapp notifications
.\.venv\Scripts\python.exe manage.py startapp education
```

`venv` isola pacotes. `startproject config .` cria `manage.py`, settings, URLs e WSGI no diretório atual. `startapp` cria o esqueleto de cada domínio. Depois registraríamos apps próprios e terceiros em `config/settings.py` e congelaríamos faixas em `requirements.txt`.

### Ordem dos arquivos centrais

1. `manage.py`: já vem do startproject e executa comandos.
2. `config/settings.py`: apps, middleware e opções.
3. `config/urls.py`: por enquanto apenas Admin.
4. `config/wsgi.py`: entrada do servidor.

Ainda não precisamos de Celery ou frontend. Primeiro provamos que Django inicia.

### Como testar

```powershell
python manage.py check
python manage.py runserver
```

Abra `http://localhost:8000/admin/`. Um erro de app não encontrado normalmente significa nome incorreto em `INSTALLED_APPS` ou ambiente sem dependência.

### Checkpoint

- `manage.py check` não apresenta erros;
- o servidor inicia;
- você sabe por que `config` é configuração e `studies` é domínio.

## Etapa 3. Modelar usuário e PostgreSQL

### Objetivo

Definir identidade antes que outros models criem ForeignKeys para ela.

### Por que esta etapa vem cedo

Trocar `AUTH_USER_MODEL` depois de muitas migrations é trabalhoso. Na reconstrução, criaríamos `users.User` antes da primeira migration do projeto.

### Pensando no banco

Perguntas anteriores ao model:

- identificador de login: o projeto usa `username` herdado;
- e-mail pode repetir? Não: `unique=True`;
- preferências são uma lista por usuário? Não: exatamente uma, portanto OneToOne;
- apagar usuário apaga preferências/estudos? Sim, relações usam cascade.

Código mínimo em `backend/users/models.py`:

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
```

Em `config/settings.py`, antes de migrar:

```python
AUTH_USER_MODEL = "users.User"
```

Para PostgreSQL, instalaríamos/criaríamos banco e preencheríamos `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST` e `DATABASE_PORT`. `python-dotenv` carrega `backend/.env`; o example documenta nomes, não segredos.

### Ciclo de migration na prática

```text
editar models.py
→ makemigrations compara estado dos models
→ arquivo Python descreve operações
→ revisar arquivo/SQL
→ migrate aplica no banco e registra histórico
```

```powershell
python manage.py makemigrations users
python manage.py sqlmigrate users 0001
python manage.py migrate
python manage.py showmigrations
```

### Como testar

```powershell
python manage.py createsuperuser
python manage.py shell
```

No shell, crie/consulte um User e confirme que senha usa `set_password/create_user`, nunca texto puro.

### Erros comuns

- Migrar o User padrão e só depois trocar `AUTH_USER_MODEL`.
- Versionar `.env`.
- Usar SQLite por conveniência e esquecer diferenças do PostgreSQL; neste projeto SQLite é apenas configuração de teste.

### Checkpoint

Você deve conseguir entrar no Admin e explicar unique, OneToOne, ForeignKey, cascade e migration.

## Etapa 4. Construir a primeira API completa: estudos

### Objetivo

Entregar uma funcionalidade vertical antes de expandir o sistema.

### Por que model primeiro

A API precisa saber qual estrutura valida e persiste. A sequência é:

```text
Study model → migration → serializer → viewset → router → teste HTTP
```

### Passo 1: model

Em `backend/studies/models.py`, começaríamos pelos campos essenciais: user, date, duration, subject e notes. Depois acrescentaríamos timestamps, ordering e índices após observar consultas reais. `MinValueValidator(1)` impede sessão zero no domínio, não apenas na UI.

### Passo 2: serializer

Em `backend/studies/serializers.py`, `StudySerializer` expõe campos de negócio, deixa ID/timestamps somente leitura e omite user. Essa omissão é intencional: o cliente não escolhe o dono.

### Passo 3: view e autorização

Versão mínima:

```python
class StudyViewSet(viewsets.ModelViewSet):
    serializer_class = StudySerializer

    def get_queryset(self):
        return Study.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

Começamos com CRUD e isolamento. Depois adicionamos `StudyFilter`, `IsStudyOwner`, calendar/statistics e services. Separar agregações em `services.py` mantém a view como coordenadora HTTP.

### Passo 4: URL

`studies/urls.py` registra DefaultRouter e `config/urls.py` inclui sob `/api/studies/`. Router evita escrever manualmente seis rotas CRUD.

### Como testar durante a construção

Primeiro teste serializer/model; depois API autenticada; por fim isolamento:

1. usuário A cria estudo;
2. resposta não aceita user arbitrário;
3. usuário B não lista nem recupera o registro;
4. duração zero retorna 400;
5. PATCH e DELETE do dono funcionam.

Use os testes atuais de `backend/tests/test_studies.py` como especificação do resultado final.

### Checkpoint

Antes do frontend, confirme CRUD pelo Swagger/APIClient. Se a API não funciona sozinha, React apenas esconderá a origem do erro.

## Etapa 5. Adicionar cadastro, JWT e permissões

### Objetivo

Permitir criar conta, entrar e proteger recursos.

### Evolução da funcionalidade

1. `RegisterSerializer` valida username/e-mail/senha e chama `create_user`.
2. `RegisterView` usa AllowAny; sem isso, a permissão global bloquearia quem ainda não tem conta.
3. SimpleJWT fornece login e refresh.
4. `REST_FRAMEWORK` define JWTAuthentication e IsAuthenticated por padrão.
5. `MeView`, mudança de senha e desativação usam `request.user`.
6. Querysets/permissions implementam autorização por ownership/role.

```text
cadastro → senha hasheada
login → access curto + refresh longo
request privada → Bearer access → request.user
→ queryset/permission decide o que esse usuário pode fazer
```

### Como testar

Teste registro inválido, senha errada, token inválido, endpoint privado anônimo, refresh e tentativa de atualizar flags administrativas. Depois teste diferença entre 401 e 403.

### Decisão importante

O projeto atual possui endpoint de refresh, mas o frontend não o usa automaticamente. Numa reconstrução fiel, documente essa limitação; não implemente rotação/blacklist como se já existisse.

### Checkpoint

Você deve obter tokens via login, chamar `/api/auth/me/` com Bearer e receber 401 sem ele.

## Etapa 6. Criar o frontend React mínimo

### Objetivo

Ter uma aplicação Vite que renderiza, navega e possui testes básicos antes de chamar a API.

### Inicialização

Na raiz, sem reutilizar o diretório frontend previamente criado:

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-router-dom
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitest/coverage-v8
npm run dev
```

O primeiro comando baixa o scaffolder oficial do ecossistema Vite, cria package.json, index.html e src inicial para React. Depois observaríamos se a página inicial abre antes de apagar o conteúdo de demonstração.

### Ordem de construção dos arquivos

1. `frontend/index.html`: idioma, título, favicon, root e script.
2. `src/main.jsx`: CSS global, BrowserRouter, provider e App.
3. `src/App.jsx`: raiz, rotas públicas/privadas e fallback `*`; `src/pages/not-found.jsx`: página 404 com retorno válido.
4. `src/components/Layout.jsx` e Sidebar: casca reutilizável.
5. páginas estáticas mínimas: login, dashboard e estudos.
6. somente depois: services, estado assíncrono e formulários.

### Construindo Layout em versões

**Versão 1 — composição:**

```jsx
export default function Layout() {
  return <main><Outlet /></main>;
}
```

Primeiro verificamos rotas aninhadas. **Versão 2:** adicionamos Sidebar. **Versão 3:** lemos `user/loading` e redirecionamos. **Versão 4:** adicionamos `open`, botão mobile e efeito que fecha o drawer na navegação. **Versão 5:** aplicamos media queries e testes de guarda.

Por que evoluir assim? Se começarmos com autenticação, drawer, CSS e roteamento juntos, não saberemos qual parte quebrou o Outlet.

### Como testar

- `/login` renderiza sem Layout;
- `/dashboard` sem user redireciona;
- com contexto autenticado, sidebar e conteúdo aparecem;
- `/` redireciona à dashboard, enquanto uma rota desconhecida mostra o 404 e oferece retorno;
- menu fecha ao navegar.

### Checkpoint

Você consegue navegar por telas ainda sem dados reais e explicar main → App → Layout → Outlet.

## Etapa 7. Criar CSS, responsividade e tema gradualmente

### Objetivo

Construir um sistema visual consistente antes de estilizar cada exceção.

### Ordem recomendada

1. reset básico: box-sizing, body sem margin, tipografia;
2. tokens claros em `:root`;
3. superfícies, botões, inputs e foco;
4. shell/sidebar/workspace;
5. padrões reutilizáveis: card, panel, hero, grids;
6. páginas/componentes;
7. breakpoints desktop-first;
8. tokens escuros;
9. testes de contraste existentes.

### Construindo o tema

Primeiro use sempre `var(--color-...)`. Depois crie `:root[data-theme="dark"]` redefinindo os mesmos tokens. Em `services/theme.js`, implemente nesta ordem:

1. `resolveTheme(preference, media)` resolve system;
2. `applyTheme` normaliza, muda `dataset.theme/colorScheme` e salva localStorage;
3. `initializeTheme` recupera antes da montagem;
4. AuthContext reaplica quando preferência do servidor muda;
5. listener de `matchMedia` reage ao sistema e possui cleanup;
6. Settings oferece select light/dark/system.

Não existe botão de tema no header; recrie o select real. Teste reload, duas preferências e mudança do sistema.

### Responsividade

Implemente primeiro desktop porque o CSS atual é predominantemente desktop-first. Reduza a janela e corrija o primeiro ponto onde conteúdo deixa de caber, em vez de escolher breakpoints aleatórios. Os resultados atuais usam 1100/980/900/760/680/400 px.

```text
base: sidebar fixa + múltiplas colunas
tablet: menos colunas e espaços
mobile: drawer + uma coluna + ações empilhadas
```

### Como saber se deu certo

Teste teclado/foco, zoom, 320 px, temas e formulários com mensagens longas. Execute testes de tema/contraste.

### Checkpoint

Nenhum componente deve precisar conhecer hexadecimais do tema; deve consumir tokens.

## Etapa 8. Ligar frontend e backend

### Objetivo

Substituir dados estáticos por requests reais com loading, sucesso, vazio e erro.

### Primeiro: os dois lados isolados

Confirme backend em 8000 e frontend em 5173. Configure CORS para a origem exata do frontend. Crie `frontend/.env`:

```text
VITE_API_URL=http://localhost:8000/api
```

### Cliente HTTP

Em `frontend/src/services/api.js`, comece apenas com `axios.create({baseURL})`. Faça um GET público/autenticado manual. Depois acrescente interceptor request para Bearer e response para 401. Separe `services/studies.js` porque componentes não devem repetir URLs/métodos.

### Construindo uma request real: listar estudos

```jsx
useEffect(() => {
  studiesApi.list()
    .then((response) => setItems(response.data))
    .catch(() => setError("Não foi possível carregar"))
    .finally(() => setLoading(false));
}, []);
```

Leitura: efeito roda na montagem; service chama GET; sucesso guarda array; falha guarda mensagem; finally encerra loading. A renderização escolhe loading, erro, lista ou empty state. Depois extraia filtros e `useCallback`, como em Studies atual.

### Construindo AuthContext

Versão 1 mantém user/loading. Versão 2 implementa login e localStorage. Versão 3 restaura sessão no mount. Versão 4 busca preferências em paralelo. Versão 5 ouve evento de 401. Teste cada evolução antes da próxima.

### Formulário de Study

Construa primeiro criação; depois use `useParams` para edição. Reaproveitar o mesmo form evita divergência de campos. Valide mínimo no HTML, mas mantenha serializer como autoridade.

### Checkpoint

Crie um estudo na UI, confirme no GET/API/Admin e verifique que outro usuário não o acessa.

## Etapa 9. Adicionar estatísticas e preferências

### Objetivo

Expandir a primeira fatia sem misturar agregação com view HTTP.

### Sequência

1. Escreva testes de exemplos: dois estudos no mesmo dia, dias consecutivos, usuário vazio.
2. Implemente `calendar_summary` e `study_statistics` em `studies/services.py`.
3. Exponha actions do ViewSet.
4. Crie `studiesApi.calendar/statistics`.
5. Construa Calendar e Statistics com loading/erro.
6. Crie UserPreferences OneToOne, migration, serializer/view e tela Settings.

Serviço vem antes do componente porque podemos verificar regra de streak sem navegador. Componentes de dashboard são criados depois para apenas apresentar contrato estável.

### Checkpoint

Resultados da API e da interface devem ignorar estudos de outros usuários e respeitar timezone do Django.

## Etapa 10. Adicionar lembretes com Celery e Redis

### Objetivo

Retirar envio periódico do ciclo HTTP e executá-lo em background.

### Por que não começar por Redis

Redis não é requisito para o CRUD principal. Primeiro comprovamos e-mail manual com `send_study_reminder`; depois criamos settings; por fim automatizamos. Isso isola SMTP de scheduler/broker.

### Ordem

1. Instale Celery/redis e crie `config/celery.py` + import em `config/__init__.py`.
2. Configure `CELERY_BROKER_URL`, result backend e timezone.
3. Crie `UserNotificationSettings` e migration.
4. Crie service de e-mail e endpoint `/test/`.
5. Crie `@shared_task check_study_reminders`.
6. Adicione schedule de 60 s.
7. Execute worker e beat separados.
8. Teste fuso, atraso, duplicidade e falha SMTP.

```text
request salva preferência (rápida)
beat publica mensagem → Redis → worker consulta banco → SMTP
```

### Como testar

Use backend de e-mail em memória e Celery eager nos testes, como `settings_test.py`. Em integração local, observe logs de beat e worker. Não espere horário real em teste automatizado: congele/mocke `timezone.now`.

### Checkpoint

Um envio que falha não pode marcar o dia como enviado; duas execuções no mesmo dia não podem duplicar.

## Etapa 11. Evoluir o domínio educacional em camadas

### Objetivo

Construir o maior domínio sem criar todas as tabelas/endpoints de uma vez.

### Ordem de modelagem

1. currículo: EducationLevel → Grade → Subject/GradeSubject → Unit → Topic;
2. conteúdo: Lesson → Example → Exercise → ExerciseChoice;
3. experiência: attempts e progress;
4. diagnóstico;
5. perfil professor/aluno, Classroom e Membership;
6. Assignment e respostas.

Para cada camada repita model → migration → Admin/seed → serializer → queryset/view → URL → testes. Defina constraints ao modelar: slug por escopo, pares únicos, `PROTECT` quando histórico não deve perder referência e status de publicação.

### Conteúdo e segurança do gabarito

Antes de listar exercícios, decida que `is_correct` não pode sair. Crie serializer público sem esse campo. Só então implemente actions answer/reveal e `check_answer`. Teste resposta JSON de listagem, não apenas model.

### Turmas e atividades

Implemente perfil/papel antes de criar turma. Depois membership/código, ownership do professor, atividades e relatório. Cada queryset deve começar pela relação do usuário, não buscar tudo e filtrar no frontend.

### Qualidade curricular

Seeds e commands vêm depois do schema estável. Use slugs e `update_or_create` para idempotência. Adicione auditoria antes de publicar. Não copie cegamente o código legado de recommendation/review: ele referencia `Child` removido e não está roteado.

### Como testar

O projeto atual não possui testes education; numa reconstrução cuidadosa, não avance sem testes de publicação/gabarito, progresso, papéis, ownership, diagnóstico e assignment. Esta é uma melhoria de processo recomendada, não uma cobertura existente.

### Checkpoint

Usuário comum não escreve currículo; professor só administra turma própria; aluno só acessa entrega própria; listagens não revelam gabarito.

## Etapa 12. Containerizar gradualmente

### Objetivo

Reproduzir ambiente somente depois de saber executar cada processo diretamente.

### Sequência de Dockerfile

Comece pelo backend. Para cada linha, pergunte:

- `FROM`: qual runtime? Sem ele não há Python/sistema base.
- `WORKDIR`: onde comandos/arquivos vivem? Sem ele caminhos ficam dispersos.
- `COPY requirements` + `RUN pip install`: dependências em camada cacheável; sem install imports falham.
- `COPY . .`: código da aplicação; sem ele só existem dependências.
- `EXPOSE`: documentação da porta; sem publicação Compose o host ainda não acessa.
- `CMD`: processo padrão; sem ele container encerra sem servidor.

Faça o mesmo para Node com package/lock e `npm ci`.

### Compose em evoluções

1. `db` + volume + healthcheck;
2. `backend` com host `db`, bind mount e migrate/runserver;
3. `redis` com AOF/healthcheck;
4. worker e beat reutilizando imagem backend;
5. frontend, node_modules volume e URL acessível pelo navegador.

Dentro da rede, `localhost` significa o próprio container; por isso backend usa `db` e `redis`. Já `VITE_API_URL` executa no navegador do host e usa `localhost:8000`.

### Como testar

```bash
docker compose --env-file backend/.env config --quiet
docker compose --env-file backend/.env up --build
docker compose ps
docker compose logs -f
```

Teste persistência: recrie container sem `down -v` e confirme dados. Não use `down -v` em dados importantes.

### Checkpoint

Seis serviços devem ficar saudáveis/iniciados, frontend deve chamar API e worker deve acessar banco/Redis.

## Etapa 13. Testar, construir e preparar produção

### Objetivo

Transformar “funciona na minha máquina” em artefatos e configurações verificáveis.

### Testes contínuos

Em cada feature, escreva regra isolada e cenário HTTP/UI. Antes de produção:

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest

cd ../frontend
npm test
npm run build
```

`npm run build` é diferente de dev: produz assets otimizados em `dist`, sem HMR. Sirva com `npm run preview` para inspeção local.

### Checklist de produção coerente com o projeto

- `DEBUG=False`, SECRET_KEY forte, hosts/origens HTTPS reais;
- `VITE_API_URL` pública terminando em `/api`;
- URL PostgreSQL secreta, SSL exigido pelo settings atual;
- migrations executadas por processo controlado;
- estratégia de staticfiles para Admin/Swagger;
- servidor WSGI de produção em vez de runserver;
- processo contínuo para worker/beat e Redis se lembretes forem requisito;
- SMTP de produção;
- logs/monitoramento/backups.

Esses itens são necessidades de preparação. O repositório atual não confirma servidor produtivo, pipeline de migrations, staticfiles, monitoramento ou hospedagem contínua de Celery.

### Checkpoint

Testes e build passam em ambiente autorizado; secrets não aparecem no bundle/repo; um restore de banco foi planejado/testado.

## Etapa 14. Git e caminho até o deploy

### Objetivo

Publicar uma versão rastreável sem confundir Git com plataforma de execução.

```text
git status → revisar diff → git add arquivos intencionais
→ git commit → git push → GitHub
→ plataforma (se conectada) instala/builda/publica
```

Na Vercel, uma configuração comum seria root frontend, `npm run build`, output `dist` e env; para Django seria necessária adaptação serverless. Porém não há configuração versionada suficiente para ensinar comandos exatos do deploy atual. Não trate a pasta local `.vercel` como infraestrutura compartilhável.

### Como saber se deu certo

Teste URL pública, refresh de rota React, CORS, login, banco, Admin/Swagger e lembrete. Deploy bem-sucedido no painel não garante que migrations ou Celery funcionem.

### Checkpoint

Você deve conseguir voltar do domínio público até commit, build e variáveis que originaram a versão, sem expor secrets.

# Ligando frontend e backend: roteiro resumido

```text
API passa nos testes sozinha
→ UI navega com dados estáticos
→ CORS e VITE_API_URL
→ Axios baseURL
→ primeira request GET
→ loading/sucesso/erro/vazio
→ POST/PATCH/DELETE
→ JWT no interceptor
→ guarda de rota/contexto
→ testes de isolamento ponta a ponta
```

Por que separar service? Para centralizar contrato HTTP e permitir que página pense em interface. Por que Context? Porque identidade interessa a muitos ramos. Por que banco? Porque dados precisam sobreviver ao processo. Por que Redis? Aqui, para transportar tarefas Celery — não para cache. Por que env? Para variar endereços/segredos sem alterar código. Por que build? Para transformar módulos de desenvolvimento em assets otimizados distribuíveis.

# Como investigar quando algo dá errado

## Processo de debug

```text
observar o sintoma e mensagem completa
→ reproduzir com passos mínimos
→ decidir: navegador, HTTP, Django, banco ou worker?
→ inspecionar a fronteira anterior
→ criar teste que falha
→ fazer a menor correção
→ executar teste e fluxo novamente
```

### Isolando por camada

1. Página branca: Console/Network, import quebrado, `#root` e erro de render.
2. UI sem dados: veja request no Network. Se não saiu, effect/service; se saiu, status/body.
3. 401: token/header/expiração. 403: papel/ownership. 404: URL ou queryset ocultando objeto.
4. 500: traceback/log Django; reproduza endpoint sem React.
5. Banco: settings/host/porta/credencial/migration. Dentro do Docker, use `db`, não localhost.
6. Lembrete: primeiro endpoint manual SMTP; depois broker; depois worker; por último beat/horário.
7. Build funciona em dev e falha: imports case-sensitive, env de build ou acesso indevido a API do navegador.

Problemas reais já identificados — recommendation/review com `child` removido e rota result deslocada — devem virar testes de regressão antes de correção, mas esta tarefa não altera código.

# Desafio: reconstruir o projeto

Tente sem copiar arquivos inteiros; consulte o guia após cada tentativa.

### Fase 1 — fundação

Crie monorepo, Django, React/Vite, PostgreSQL e env examples. Entrega: os dois servidores iniciam.

### Fase 2 — primeira fatia

Implemente User, JWT e Study CRUD isolado por usuário. Entrega: testes API verdes.

### Fase 3 — interface

Implemente App, AuthContext, Layout, login e páginas de Study. Entrega: cadastro→login→criação→lista.

### Fase 4 — experiência

Implemente dashboard, Calendar, Statistics, Settings, tema e responsividade. Entrega: mobile/light/dark e estados de erro.

### Fase 5 — processos auxiliares

Implemente settings de notificação, SMTP manual, Redis/Celery/Beat. Entrega: envio único por dia local.

### Fase 6 — educação

Modele currículo em camadas, publique conteúdo seguro, progresso, diagnóstico, turma e assignments. Entrega: testes de gabarito/roles/ownership.

### Fase 7 — infraestrutura

Crie Dockerfiles/Compose, volumes e healthchecks. Entrega: ambiente novo sobe com um comando e preserva banco.

### Fase 8 — produção

Faça build, configure domínios/env/migrations/staticfiles/workers, publique e execute smoke tests. Como a configuração real está incompleta no repo, escolha/documente uma plataforma compatível em seu exercício.

# Ordem recomendada para estudar este projeto

1. Leia visão geral, arquitetura e árvore.
2. Abra `index.html`, `main.jsx` e `App.jsx`.
3. Estude JSX, props, state, effects e eventos nos componentes pequenos.
4. Estude Layout, Router e Context.
5. Estude CSS tokens, Grid/Flexbox, tema e responsividade.
6. Siga Axios/services e um CRUD completo de Study.
7. Aprenda URL → view → serializer → model/service no Django.
8. Desenhe relações PostgreSQL e percorra migrations.
9. Estude JWT e authorization/ownership.
10. Estude regras educacionais e seus pontos de atenção.
11. Estude Celery/Redis/SMTP.
12. Leia Dockerfiles e depois Compose.
13. Execute testes/build.
14. Compare desenvolvimento, produção e lacunas de deploy.
15. Refaça o desafio em branch/repositório separado.

## 22. Exercícios práticos de estudo

Faça em uma branch ou apenas leia/simule quando não quiser alterar arquivos.

1. Abra `frontend/index.html` e identifique o nó que recebe React, idioma, título e favicon.
2. Em `frontend/src/main.jsx`, desenhe a árvore de providers do mais externo ao mais interno.
3. Em `frontend/src/App.jsx`, compare `/`, `/studies/15/edit` e `/caminho-inexistente`: descreva redirecionamento, componentes montados e guarda de autenticação em cada caso.
4. Em `Calendar.jsx`, altere mentalmente mês/ano e explique por que a API é chamada novamente.
5. Em `StatCard.jsx`, liste quais valores vêm por props e qual possui default.
6. Use DevTools para mudar temporariamente `data-theme` do `<html>` e observe quais tokens CSS entram em ação.
7. Localize uma regra Flexbox e uma Grid em `global.css`; desative cada `display` no inspetor e compare o layout.
8. Siga `studiesApi.create` até `StudyViewSet.perform_create` e anote cada arquivo atravessado.
9. Compare um 401 com um 403: localize o tratamento do primeiro no Axios e uma regra que produz o segundo no backend.
10. Rode `python manage.py showmigrations` quando tiver ambiente Python e identifique quais apps possuem pendências.
11. Leia `docker-compose.yml` e faça uma tabela separando portas acessíveis pelo host e apenas pela rede interna.
12. Execute `npm test` e escolha um teste de Calendar para explicar Arrange, Act e Assert.
13. Descubra por que o refresh token persistido não renova automaticamente a sessão.
14. Compare `GET /api/studies/` e `GET /api/education/questions/` quanto a escopo/visibilidade.
15. Sem corrigir, explique por que `recommendation_service.py` ficou incompatível após a migration 0013.

## 23. Gabarito das perguntas de revisão

### Frontend

1. Porque React produzirá a árvore dentro dele após `main.jsx`; o HTML inicial só fornece o ponto de montagem.
2. Props vêm do pai e são entradas, como dados de StatCard; state é memória mutável via setter, como mês/dados de Calendar.
3. Porque a consulta mensal depende desses valores e precisa ser refeita quando qualquer um mudar.
4. App aninha páginas sob Layout; Layout verifica loading/user antes de renderizar o Outlet.
5. Os nomes dos tokens permanecem, mas seus valores são redefinidos pelo seletor `:root[data-theme="dark"]`.
6. Link navega declarativamente; NavLink também conhece estado ativo; Navigate redireciona durante render; useNavigate navega dentro de funções/eventos.
7. Porque `value` vem do estado React e todo `onChange` atualiza esse estado.
8. Flexbox aparece em shell/heroes/registros/ações; Grid em filtros, cards, configurações e campos de formulário.

### Backend e banco

1. URL resolve caminho; view coordena request; serializer valida/converte; service encapsula regra; model representa/persiste dados.
2. O filtro impede até listar/buscar dados alheios; a permission é uma segunda regra explícita no objeto.
3. Garante que gravações relacionadas sejam confirmadas juntas ou revertidas em falha.
4. Study→User é ForeignKey; Preferences→User é OneToOne; Classroom→students e Assignment→exercises são ManyToMany com models intermediários.
5. Para que todos os ambientes reproduzam a mesma evolução de schema de modo ordenado.
6. `StudyViewSet.get_queryset()` limita por `request.user`, `perform_create` define o dono e `IsStudyOwner` verifica o objeto.

### Docker

1. Imagem é o molde; container é a instância; serviço é a definição Compose que cria/configura containers.
2. O DNS interno resolve o nome do serviço; fora da rede, o host acessa a porta publicada em localhost.
3. Os arquivos de dados do PostgreSQL montados em `/var/lib/postgresql/data`.
4. Para reutilizar a camada de instalação enquanto requirements não mudar.
5. EXPOSE documenta a porta da imagem; `ports` cria o mapeamento real host-container.

## 24. Referências auditadas

Principais arquivos: `README.md`, `docs/API.md`, `docs/EDUCATION_CONTENT.md`, `.gitignore`, `docker-compose.yml`; todo `backend/config`; requirements/Dockerfile/examples de ambiente; models, serializers, views, URLs, permissions, services, tasks, admin, migrations, tests e management commands dos quatro apps; `frontend/package.json`, Vite/Docker/env, `src/main.jsx`, `App.jsx`, context, hook, services, páginas — incluindo `not-found.jsx` —, componentes, estilos e testes.

Partes não encontradas ou impossíveis de confirmar: provedor real do banco e Redis de produção, pooling externo, configuração reproduzível Vercel, comando de deploy/migrations, servidor produtivo, CI/CD, terminação HTTPS detalhada, monitoramento, rate limiting, cache, Channels/WebSockets, mídia e cobertura percentual atual.

Para esses itens, **não foi possível confirmar isso pelos arquivos atuais do projeto**.

Nenhum dado inventado: **confirmado**. Suposições de configuração não confirmadas foram identificadas como tais.
