# Conteúdo educacional

O currículo é global e compartilhado. A hierarquia é `EducationLevel → Grade → GradeSubject → Unit → Topic → Lesson → Example/Exercise`. `Child`, `TopicProgress`, `LessonProgress` e `ExerciseAttempt` armazenam somente a experiência individual; nunca é criada uma cópia do currículo por filho.

## Publicação e qualidade

Um outline pode ser importado como rascunho. Somente tópicos com introdução, contexto (`Lesson.importance`), explicação, orientação, exemplos, exercícios com gabarito e explicação e revisão (`Lesson.summary`) podem permanecer publicados. Execute:

```text
python manage.py audit_education_content
python manage.py audit_education_content --unpublish-incomplete
python manage.py validate_education
```

O primeiro comando falha se houver material incompleto publicado. O segundo preserva o registro e o histórico, alterando apenas seu status para rascunho. Nunca publique placeholders para aumentar artificialmente a cobertura.

## Seeds e atualizações

Os arquivos ficam em `education/seed_data`, separados por etapa, série e disciplina. Use slugs estáveis. `seed_education` usa `update_or_create`, preserva IDs quando encontra a mesma chave e não apaga tentativas ou progresso. Pode ser limitado por série com `--grade`, por exemplo `--grade=fundamental-ii:7-ano`. Antes de substituir material, mantenha o registro anterior como rascunho/revisão quando houver histórico.

Para adicionar uma disciplina, reutilize `Subject` pelo slug e crie o vínculo `GradeSubject`. Para adicionar conteúdo, reutilize a unidade e identifique o tópico por slug dentro da matéria/série. A versão curricular pertence a `Curriculum`, associada ao `GradeSubject`, às habilidades e aos objetos de conhecimento.

## Carregamento progressivo

- `/learn` busca filhos, níveis, séries e apenas as matérias da série escolhida.
- A matéria busca suas unidades e `/topics/?grade_subject=<id>`; a lista não inclui aulas nem exercícios.
- O tópico busca apenas seu detalhe, `/topics/<id>/lessons/`, seus irmãos por `/topics/?unit=<id>` e exercícios paginados.
- `/topics/<id>/exercises/?page=1&page_size=20` limita o tamanho do payload; o máximo é 50.
- O progresso pode ser limitado por `topic` ou `grade_subject` e sempre exige o filho pertencente ao usuário.

As queries curriculares usam `select_related`, `prefetch_related` e `annotate` nos caminhos de leitura. Listas nunca expõem alternativas corretas. Cache futuro deve conter somente currículo público/global; progresso, tentativas e dados de filhos não devem ser compartilhados ou armazenados sob chaves globais. Qualquer cache curricular deve ser invalidado pelo seed e por alterações administrativas antes de ser ativado em produção.

## Preservação de histórico

Não remova `Topic`, `Lesson` ou `Exercise` que possuam progresso ou tentativas. Atualize pelo identificador estável e publique uma nova versão somente depois da auditoria. Mudanças de série do filho não alteram nem apagam registros anteriores.
