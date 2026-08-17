# API do Study Tracker

Referência das rotas registradas no projeto. Com o backend em execução, a documentação OpenAPI fica em `/api/docs/` e o schema em `/api/schema/`.

Exceto no cadastro e na obtenção ou renovação de tokens, envie:

```http
Authorization: Bearer <access_token>
```

## Autenticação e conta

| Método | Rota | Finalidade |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Criar conta |
| `POST` | `/api/auth/login/` | Obter access e refresh tokens |
| `POST` | `/api/auth/refresh/` | Renovar o access token |
| `GET`, `PATCH` | `/api/auth/me/` | Consultar ou atualizar o perfil |
| `POST` | `/api/auth/change-password/` | Alterar a senha |
| `DELETE` | `/api/auth/account/` | Desativar a própria conta |
| `GET`, `PATCH` | `/api/users/preferences/` | Consultar ou atualizar preferências |

## Estudos e notificações

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET`, `POST` | `/api/studies/` | Listar ou criar estudos |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/studies/{id}/` | Operar um estudo do usuário |
| `GET` | `/api/studies/calendar/?month={mês}&year={ano}` | Resumo diário do mês |
| `GET` | `/api/studies/statistics/` | Totais, médias e sequências |
| `GET`, `PATCH` | `/api/notifications/settings/` | Configurar o lembrete diário |
| `POST` | `/api/notifications/test/` | Enviar um lembrete de teste |

A listagem de estudos aceita `start_date`, `end_date`, `month`, `year` e `subject`.

## Currículo e conteúdo

Os recursos curriculares usam as operações padrão de listagem, criação, consulta, substituição, alteração parcial e exclusão. Escritas exigem usuário `staff`.

| Recurso | Rota base | Operações adicionais |
| --- | --- | --- |
| Níveis | `/api/education/levels/` | — |
| Séries | `/api/education/grades/` | `GET /{id}/subjects/` |
| Matérias | `/api/education/subjects/` | `GET /{id}/units/` |
| Conteúdos | `/api/education/topics/` | `GET /{id}/lessons/`, `GET /{id}/exercises/`, `GET /{id}/progress/`, `POST /{id}/diagnostic/start/` |
| Aulas | `/api/education/lessons/` | `POST /{id}/complete/` |
| Exercícios | `/api/education/exercises/` | `POST /{id}/answer/`, `POST /{id}/reveal/` |

Conteúdos aceitam `grade_subject` e `unit`; unidades aceitam `grade`. Exercícios por conteúdo aceitam paginação opcional por `page` e `page_size`.

## Progresso, perfil e turmas

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET` | `/api/education/progress/` | Listar progresso; aceita `topic` e `grade_subject` |
| `GET`, `PATCH` | `/api/education/profile/` | Consultar ou definir perfil educacional |
| `GET`, `POST` | `/api/education/classrooms/` | Listar ou criar turmas |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/education/classrooms/{id}/` | Consultar ou administrar turma |
| `POST` | `/api/education/classrooms/join/` | Entrar por código |
| `POST` | `/api/education/classrooms/{id}/join/` | Entrar pelo identificador |
| `POST` | `/api/education/classrooms/{id}/leave/` | Sair da turma |
| `GET`, `POST` | `/api/education/classrooms/{id}/activities/` | Listar ou criar atividades |
| `GET` | `/api/education/classrooms/{id}/performance/` | Consultar desempenho |

Criar turma exige perfil de professor. Administrar a turma, publicar atividades e consultar desempenho exige ser o professor responsável.

## Diagnóstico e atividades

| Método | Rota | Finalidade |
| --- | --- | --- |
| `POST` | `/api/education/topics/{id}/diagnostic/start/` | Iniciar diagnóstico |
| `POST` | `/api/education/diagnostics/{id}/answer/` | Registrar resposta |
| `POST` | `/api/education/diagnostics/{id}/finish/` | Finalizar diagnóstico |
| `GET` | `/api/education/diagnostics/{id}/result/` | Consultar resultado próprio |
| `GET` | `/api/education/questions/` | Consultar banco de questões |
| `GET`, `POST` | `/api/education/assignments/` | Listar ou criar atividades |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/education/assignments/{id}/` | Consultar ou administrar atividade |
| `POST` | `/api/education/assignments/{id}/start/` | Iniciar ou retomar entrega |
| `GET` | `/api/education/assignments/{id}/results/` | Consultar resultados autorizados |
| `GET` | `/api/education/student-assignments/{id}/` | Consultar a própria entrega |
| `POST` | `/api/education/student-assignments/{id}/answer/` | Salvar resposta |
| `POST` | `/api/education/student-assignments/{id}/submit/` | Entregar e calcular resultado |

O banco de questões aceita filtros curriculares, dificuldade e tipo. A visibilidade das atividades depende da relação do usuário com a turma.
