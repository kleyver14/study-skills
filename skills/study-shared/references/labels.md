# Labels — fixed text of the templates, per language

The templates in `templates/` use `{{h_*}}` for short labels and `{{txt_*}}` for fixed prose.
Fill them from this file using the plan's `language:`. Do not translate them yourself: that is
what this file is for, and it keeps every plan consistent. If the language is not here, follow
`language.md`, *Supported languages*.

Which language goes where (plan vs conversation, unsupported languages, neutral Spanish) is in
`language.md`.

`study_state.py check` fails on any `{{placeholder}}` left in a plan, so every key used by a
template must exist below.

## Short labels

| key | es | en | pt |
|---|---|---|---|
| h_session | Sesión | Session | Sessão |
| h_block | Bloque | Block | Bloco |
| h_reading | Lectura | Reading | Leitura |
| h_videos | Videos | Videos | Vídeos |
| h_optional | opcional | optional | opcional |
| h_topic | Tema | Topic | Tema |
| h_what_to_study | Qué estudiar | What to study | O que estudar |
| h_how_to_think | Cómo pensarlo | How to think about it | Como pensar nisso |
| h_readings | Lecturas | Readings | Leituras |
| h_col_resource | Recurso | Resource | Recurso |
| h_col_link | Link | Link | Link |
| h_col_time | Tiempo | Time | Tempo |
| h_col_class | Clase | Class | Aula |
| h_col_course | Curso | Course | Curso |
| h_col_duration | Duración | Duration | Duração |
| h_covers | Cubren | Covers | Cobrem |
| h_not_covered | No cubren | Not covered | Não cobrem |
| h_stick_to_reading | quédate con la lectura | stick to the reading | fique com a leitura |
| h_practice | Práctica | Practice | Prática |
| h_evaluation | Evaluación | Evaluation | Avaliação |
| h_threshold | Umbral | Threshold | Limiar |
| h_result | Resultado | Result | Resultado |
| h_notes | Apuntes — lo que entendí | Notes — what I understood | Anotações — o que entendi |
| h_weak | Lo que quedó flojo | What is still weak | O que ficou fraco |
| h_eval_session | Evaluación de la sesión | Session evaluation | Avaliação da sessão |
| h_eval_checkpoint | Punto de control | Checkpoint | Ponto de controle |
| h_eval_mock | Simulacro | Mock exam | Simulado |
| h_eval_integrative | Evaluación integradora | Integrative evaluation | Avaliação integradora |
| h_state | Estado actual | Current state | Estado atual |
| h_how_to_use | Cómo usar esto | How to use this | Como usar isto |
| h_calendar | Calendario | Calendar | Calendário |
| h_syllabus | Temario aprobado | Approved syllabus | Conteúdo aprovado |
| h_baseline | Línea base | Baseline | Linha de base |
| h_concepts | Conceptos a corregir | Concepts to fix | Conceitos a corrigir |
| h_params | Parámetros del protocolo | Protocol parameters | Parâmetros do protocolo |
| h_log | Registro de evaluaciones | Evaluation log | Registro de avaliações |
| h_closures | Cierres de bloque | Block closures | Fechamentos de bloco |
| h_sources | Fuentes | Sources | Fontes |
| h_appendix | Anexo — checklist final | Appendix — final checklist | Anexo — checklist final |
| h_diagnostic | Diagnóstico | Diagnostic | Diagnóstico |
| h_date | Fecha | Date | Data |
| h_declared_level | Nivel declarado | Declared level | Nível declarado |
| h_mode | Modo | Mode | Modo |
| h_result_by_area | Resultado por área | Result by area | Resultado por área |
| h_overall | Total | Overall | Total |
| h_reading_of_result | Lectura del resultado | What the result says | Leitura do resultado |
| h_order_decision | Decisión sobre el orden del plan | Decision on plan order | Decisão sobre a ordem do plano |
| h_questions | Preguntas y respuestas | Questions and answers | Perguntas e respostas |

## Table header rows

Use these as the first two lines of the tables (they are also what `study_state.py log` appends under).

| key | es | en | pt |
|---|---|---|---|
| tbl_concepts | `\| # \| Concepto \| Error cometido \| Se enseña en \| Estado \| Último cambio \|` | `\| # \| Concept \| Error made \| Taught in \| Status \| Last change \|` | `\| # \| Conceito \| Erro cometido \| Ensinado em \| Estado \| Última mudança \|` |
| tbl_log | `\| Fecha \| Sesión \| Tipo \| Puntaje \| Aprobó \| Acertadas con ? \| Conceptos fallados \|` | `\| Date \| Session \| Type \| Score \| Passed \| Guessed right (?) \| Concepts failed \|` | `\| Data \| Sessão \| Tipo \| Nota \| Aprovou \| Acertos com ? \| Conceitos com erro \|` |
| tbl_sources | `\| Fuente \| Tipo \| Verificada \|` | `\| Source \| Kind \| Verified \|` | `\| Fonte \| Tipo \| Verificada \|` |
| tbl_areas | `\| Área \| Peso \| Preguntas \| Correctas \| Acertadas con ? \| Puntaje \|` | `\| Area \| Weight \| Questions \| Correct \| Guessed right (?) \| Score \|` | `\| Área \| Peso \| Perguntas \| Corretas \| Acertos com ? \| Nota \|` |

The second line is always `|---|` repeated for each column.

## Fixed prose

### es

- **txt_living_doc:** Documento vivo: todos los comandos `study-*` lo leen y lo actualizan. Los bloques de **estado** y **calendario** los regenera `study_state.py`; no los edites a mano.
- **txt_how_to_use:**
  1. `/study-next` abre la próxima sesión pendiente: tema, qué estudiar, cómo pensarlo, lecturas verificadas, videos y práctica opcional.
  2. Estudias por tu cuenta con ese material. Si algo no se entiende, pregunta.
  3. `/study-eval` cuando te sientas listo. Marca con `?` lo que adivines: acertar adivinando no es saber.
  4. Los errores se corrigen uno por uno, del más simple al más complejo.
  5. `/study-close`: explicas con tus palabras las 2 o 3 ideas centrales, y eso queda como apunte de la sesión.
  6. `/study-status`: dónde estás, cuánto te atrasaste y el fin proyectado a tu ritmo. `study-status replan` si cambió tu ritmo o tu fecha.

  **Para cualquier sesión de Claude que retome esto:** lee el bloque de estado y después la sesión a la que apunta. El protocolo vive en las skills `study-*`, no aquí.
- **txt_calendar_note:** Las fechas son una proyección según tu cadencia, no un compromiso. Si un día no estudias, no se salta ninguna sesión: la cola simplemente no avanza, y `study-next` reproyecta.
- **txt_concepts_note:** Cada respuesta incorrecta, o correcta pero adivinada, genera una fila. Se vuelve a preguntar en cada evaluación hasta responderla bien dos veces seguidas sin `?`, subiendo como máximo un escalón por evaluación. `pendiente → explicado → confirmado×1 → consolidado`
- **txt_params_note:** Los números viven en el frontmatter de este archivo, así hay un solo lugar donde cambiarlos.
- **txt_closures_note:** Los agrega `study-close` cuando cierra una sesión de punto de control.
- **txt_sources_note:** Tipos: **oficial** (guía de examen, documentación canónica, programa del curso) · **aportada** (por ti) · **construida** (propuesta por Claude y validada contigo) · **plataforma** (curso de video; solo título, duración y link). Cada link se verificó en la fecha indicada.
- **txt_appendix_note:** Todo el temario en una lista, para el repaso final: tienes que poder decir en una línea qué es cada cosa.
- **txt_practice_optional:** Opcional. La sesión está completa sin esto, y nunca cuenta para el umbral.
- **txt_eval_hint:** Marca con `?` lo que adivines. Cuando estés listo, `/study-eval`.
- **txt_no_eval:** Sesión de repaso: no tiene evaluación. Cuando termines, `/study-close`.
- **txt_not_taken:** Todavía no realizada.
- **txt_notes_hint:** Lo escribe `/study-close` con tus propias palabras.
- **txt_weak_hint:** Lo escribe `/study-eval` si no llegas al umbral, y lo reescribe `/study-close` al cerrar.
- **txt_videos_intro:** Opcionales pero no descartables: cubren el tema en formato visual. Su tiempo no suma al de la sesión.
- **txt_no_platform:** Sin plataforma de videos declarada.
- **txt_videos_unavailable:** Los videos no se pudieron buscar al crear el plan: la plataforma bloqueó la consulta. Pide "agrega los videos" para reintentar.
- **txt_no_video_for_topic:** Ninguna clase de los cursos elegidos cubre este tema: quédate con las lecturas.

### en

- **txt_living_doc:** Living document: every `study-*` command reads and updates it. The **state** and **calendar** blocks are regenerated by `study_state.py`; do not edit them by hand.
- **txt_how_to_use:**
  1. `/study-next` opens the next pending session: topic, what to study, how to think about it, verified readings, videos and optional practice.
  2. Study on your own with that material. Ask when something is unclear.
  3. `/study-eval` when you feel ready. Mark guesses with `?`: guessing right is not knowing.
  4. Errors are corrected one at a time, simplest first.
  5. `/study-close`: you explain the 2-3 core ideas in your own words, and that becomes the session's notes.
  6. `/study-status`: where you stand, drift and the projected end at your pace. `study-status replan` when your pace or deadline changes.

  **For any Claude session picking this up:** read the state block, then the session it points to. The protocol lives in the `study-*` skills, not here.
- **txt_calendar_note:** Dates are a projection from your cadence, not a contract. Missing a day skips nothing: the queue just does not advance, and `study-next` re-projects.
- **txt_concepts_note:** Every wrong or guessed-right answer becomes a row. It is re-asked in every evaluation until answered correctly twice in a row without `?`, moving up at most one step per evaluation. `pending → explained → confirmed×1 → consolidated`
- **txt_params_note:** The numbers live in this file's frontmatter, so there is one place to change them.
- **txt_closures_note:** Added by `study-close` when a checkpoint session closes.
- **txt_sources_note:** Kinds: **official** (exam guide, canonical docs, course syllabus) · **provided** (by you) · **built** (proposed by Claude, validated with you) · **platform** (video course; title, duration and link only). Every link was checked on the date shown.
- **txt_appendix_note:** The whole syllabus as one list, for the last review: you should be able to say in one line what each item is.
- **txt_practice_optional:** Optional. The session is complete without it, and it never counts toward the threshold.
- **txt_eval_hint:** Mark with `?` anything you guessed. When ready, `/study-eval`.
- **txt_no_eval:** Review session: no evaluation. When done, `/study-close`.
- **txt_not_taken:** Not taken yet.
- **txt_notes_hint:** Written by `/study-close`, in your own words.
- **txt_weak_hint:** Written by `/study-eval` if you miss the threshold, rewritten by `/study-close` when closing.
- **txt_videos_intro:** Optional but not throwaway: they cover the topic visually. Their time does not add to the session's.
- **txt_no_platform:** No video platform declared.
- **txt_videos_unavailable:** Videos could not be looked up when the plan was created: the platform blocked the request. Ask "add the videos" to retry.
- **txt_no_video_for_topic:** No class in the chosen courses covers this topic: stick to the readings.

### pt

- **txt_living_doc:** Documento vivo: todos os comandos `study-*` o leem e o atualizam. Os blocos de **estado** e **calendário** são regenerados por `study_state.py`; não os edite à mão.
- **txt_how_to_use:**
  1. `/study-next` abre a próxima sessão pendente: tema, o que estudar, como pensar nisso, leituras verificadas, vídeos e prática opcional.
  2. Estude por conta própria com esse material. Pergunte quando algo não ficar claro.
  3. `/study-eval` quando se sentir pronto. Marque com `?` o que chutou: acertar chutando não é saber.
  4. Os erros são corrigidos um por vez, do mais simples ao mais complexo.
  5. `/study-close`: você explica as 2 ou 3 ideias centrais com suas palavras, e isso vira a anotação da sessão.
  6. `/study-status`: onde você está, o atraso e o fim projetado no seu ritmo. `study-status replan` quando mudar seu ritmo ou prazo.

  **Para qualquer sessão do Claude que retome isto:** leia o bloco de estado e depois a sessão a que ele aponta. O protocolo vive nas skills `study-*`, não aqui.
- **txt_calendar_note:** As datas são uma projeção da sua cadência, não um compromisso. Perder um dia não pula nenhuma sessão: a fila só não avança, e `study-next` reprojeta.
- **txt_concepts_note:** Cada resposta errada, ou certa mas chutada, vira uma linha. Ela volta em cada avaliação até ser respondida corretamente duas vezes seguidas sem `?`, subindo no máximo um degrau por avaliação. `pendente → explicado → confirmado×1 → consolidado`
- **txt_params_note:** Os números ficam no frontmatter deste arquivo, assim há um só lugar para mudá-los.
- **txt_closures_note:** Adicionados por `study-close` quando fecha uma sessão de ponto de controle.
- **txt_sources_note:** Tipos: **oficial** (guia do exame, documentação canônica, programa do curso) · **fornecida** (por você) · **construída** (proposta pelo Claude e validada com você) · **plataforma** (curso em vídeo; só título, duração e link). Cada link foi verificado na data indicada.
- **txt_appendix_note:** Todo o conteúdo numa lista, para a revisão final: você deve conseguir dizer numa linha o que é cada item.
- **txt_practice_optional:** Opcional. A sessão está completa sem isto, e nunca conta para o limiar.
- **txt_eval_hint:** Marque com `?` o que chutou. Quando estiver pronto, `/study-eval`.
- **txt_no_eval:** Sessão de revisão: sem avaliação. Ao terminar, `/study-close`.
- **txt_not_taken:** Ainda não feita.
- **txt_notes_hint:** Escrito por `/study-close`, com suas palavras.
- **txt_weak_hint:** Escrito por `/study-eval` se você não atingir o limiar, e reescrito por `/study-close` ao fechar.
- **txt_videos_intro:** Opcionais, mas não descartáveis: cobrem o tema em formato visual. O tempo deles não soma ao da sessão.
- **txt_no_platform:** Nenhuma plataforma de vídeo declarada.
- **txt_videos_unavailable:** Não foi possível buscar os vídeos ao criar o plano: a plataforma bloqueou a consulta. Peça "adicione os vídeos" para tentar de novo.
- **txt_no_video_for_topic:** Nenhuma aula dos cursos escolhidos cobre este tema: fique com as leituras.

## Composed pieces

These are built from the labels above; the templates reference them by name.

- **milestones_line** (PLAN.md calendar): the external milestones in one line, e.g. es `**Hitos:** 25/09 · 09/10 (1:1)`, en `**Milestones:** Sep 25 · Oct 9 (1:1)`; the single word `—` when `milestones: null`.
- **video_line** (session header): ` · {h_videos} ~{video_minutes} min ({h_optional})` when the session has videos, empty otherwise.
- **eval_block**, for `eval_type` other than `none`:
  ```
  ## {h_evaluation} — {h_eval_<type>}

  {what the evaluation covers and its size, in the plan's language}

  - **{h_threshold}:** {threshold}%
  - {txt_eval_hint}
  ```
- **eval_block**, for `eval_type: none`: the single line `_{txt_no_eval}_`.
- **videos** (content of the Videos region):
  - with videos: `{txt_videos_intro}`, then the table with header `| {h_col_class} | {h_col_course} | {h_col_duration} | {h_col_link} |`, then the line `**{h_covers}:** … · **{h_not_covered}:** … → {h_stick_to_reading}`.
  - no class covers the topic: `_{txt_no_video_for_topic}_`
  - no platform declared: `_{txt_no_platform}_`
  - lookup blocked: `_{txt_videos_unavailable}_`
