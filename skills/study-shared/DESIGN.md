# Diseño — familia de skills `study-*`

> Especificación aprobada en conversación el 2026-09-11. Es la fuente de verdad para construir
> las skills. Si algo de la implementación contradice este documento, gana el documento o se
> actualiza el documento primero.

## 1. Propósito

Permitir que cualquier persona construya y opere un plan de estudio sobre **cualquier tema**,
con **cualquier duración y cadencia**, con la misma disciplina que tuvo un plan real de AWS
CLF-C02 armado a mano: temario sacado de fuentes verificadas, sesiones con material y
práctica, evaluaciones con umbral, corrección de errores uno por uno, apuntes con las palabras
del usuario, y seguimiento del avance legible por cualquier sesión futura.

Ese plan fue el **ejemplo de referencia**, no el molde. Las plantillas no contienen nada
específico de AWS.

## 2. Decisiones de alcance

| Decisión | Valor | Consecuencia |
|---|---|---|
| Audiencia | Cualquier persona, sola o en equipo | Se instala en `~/.claude/skills/` con `install.sh` |
| Plataforma | **Solo Claude Code** (terminal, escritorio, web) | Usa `AskUserQuestion`. No instalable en `~/.agents/skills/` para Cursor/Codex |
| Ciclo de vida | Genera **y** opera | Familia de comandos, no una skill generadora sola |
| Fuentes | Cascada: oficial → aportada por el usuario → construida y validada | Nunca se inventan URLs; todo link se verifica antes de escribirse |
| Integraciones | **Solo archivos locales** | Sin Jira ni Slack. Los resúmenes de cierre quedan listos para copiar |
| Ubicación del plan | La skill propone rutas y el usuario puede escribir la suya | Registro central en `~/.study/` |
| Unidad de tiempo | **La sesión, no el día** | Cadencia libre; los archivos no llevan fecha en el nombre |
| Seguimiento externo | **Opcional** | Sin hitos externos, la skill propone puntos de control internos rechazables |
| Horizonte | Exacto, aproximado ("unos 3 meses") o inexistente | Fin fijo · fin flexible con semana objetivo · fin abierto |
| Idioma | Estructura en inglés; contenido en el idioma del usuario | `PLAN.md`, `sessions/`, `session-NN-…` son identificadores estables |
| Videos | Platzi + pegado manual; opcionales pero no descartables | El tiempo de la sesión es solo de lecturas. Ver §12 |

## 3. Arquitectura

### 3.1 Familia de skills

```
study-new      entrevista → temario validado → diagnóstico según nivel → genera el plan
study-next     abre la próxima sesión pendiente; mide deriva; dispara recuperación
study-eval     arma y corrige evaluaciones con el protocolo
study-close    cierra la sesión con apuntes; cierra bloques
study-status   estado, deriva, proyección; cambio de plan activo; replan
study-shared   templates + references. No invocable por el usuario
```

Patrón idéntico a `sdd-*`: cada `SKILL.md` es corto y carga solo lo que su comando necesita;
las plantillas y referencias viven una sola vez en `study-shared`.

Los `SKILL.md` se escriben en **inglés** (estilo de la casa). Todo lo que se genera para el
usuario va en el idioma que eligió.

### 3.2 Registro de planes

```
~/.study/
├── plans      una línea por plan:   <slug><TAB><ruta absoluta>
└── active     el slug del plan activo (una línea)
```

Texto plano, sin dependencias. `study-next` y `study-status` lo leen; `study-new` lo escribe;
`study-status` puede cambiar `active`. Si hay varios planes y `active` está vacío, se pregunta.

### 3.3 Frontmatter de sesión — única fuente de verdad del estado

```yaml
---
session: 7                    # entero, 1-based
slug: eloquent-relaciones     # corto, kebab-case, en el idioma del plan
status: pending               # pending | studied | evaluated | closed
planned_date: 2026-09-22      # proyección; se reescribe al reproyectar
actual_date: null             # fecha en que se abrió (status pasa a studied)
block: 1                      # bloque o punto de control al que pertenece; 0 si no hay
is_buffer: false              # sesión de colchón
is_checkpoint: false          # cierra un bloque o punto de control
eval_type: session            # session | checkpoint | mock | integrative | none
eval_score: null              # "8/10"
eval_passed: null             # true | false | null
eval_attempts: 0              # primer intento + re-evaluaciones
eval_date: null
closed_date: null              # lo escribe study-close
practice_level: live          # live | sandbox | none
video_minutes: 0              # suma de la sección Videos (§12); no entra en el tiempo de la sesión
---
```

Semántica de `status`:
- `pending` — no se abrió.
- `studied` — se abrió y se entregó el material. **No** significa aprendida.
- `evaluated` — la evaluación se aprobó (o no aplica).
- `closed` — apuntes escritos.

La sección *Estado actual* de `PLAN.md` se **regenera** a partir de estos encabezados cada vez
que un comando escribe. Nunca se edita a mano.

## 4. `study-new` — crear un plan

### 4.1 Entrevista

Con `AskUserQuestion`, hasta 4 preguntas por pantalla, siempre con la opción libre "Otro".
Si la herramienta no está disponible, se pregunta lo mismo en texto plano.

**Pantalla 1 — Objetivo y fuentes**
1. Qué quieres aprender y para qué → tipo de objetivo: `exam` · `tool` · `course` · `other`.
2. ¿Existe una guía oficial? ¿Tienes material propio? → activa la cascada de fuentes.

**Paso conversacional — Temario propuesto.** La skill arma el temario desde las fuentes,
lo muestra con áreas, subtemas y (si existen) pesos oficiales, y **lo itera con el usuario
hasta que lo aprueba**. Nada se genera antes de esto.

**Pantalla 2 — Tiempo y nivel**
3. ¿Para cuándo? → fecha exacta (`fixed`) · aproximada (`flexible`, semana objetivo) · sin fecha (`open`).
4. ¿Qué días o cuántas veces por semana, y cuánto por sesión? → cadencia y tamaño de sesión.
5. ¿Empiezas de cero, sabes algo, o ya trabajas con esto? → determina el tipo de diagnóstico.

**Paso conversacional — Verificación de realidad.** Sesiones disponibles = cadencia × horizonte.
Sesiones necesarias = estimación por tamaño del temario. La skill dice si sobra, alcanza o
falta, y en el último caso propone recortar temario, subir cadencia o extender horizonte.
Con fin `open` este paso solo informa cuántas sesiones saldrán.

**Pantalla 3 — Práctica y seguimiento**
6. ¿A qué de esto tienes acceso real para practicar? → opciones = áreas del temario aprobado,
   más "a nada", con selección múltiple. `AskUserQuestion` admite 4 opciones por pregunta:
   si el temario tiene más de 4 áreas, se agrupan en hasta 4 grupos afines o se reparte en
   varias preguntas de la misma pantalla. Define `practice_level` por área.
7. ¿Tienes acceso a alguna plataforma de cursos? → Platzi · otra (pegas el índice) · ninguna.
   Selección múltiple. Activa la búsqueda de videos (§12); "ninguna" no busca nada.
8. ¿Alguien te hace seguimiento o tienes fechas de reporte? (*no es necesario*) → hitos
   externos, o puntos de control internos propuestos (rechazables).

**Pantalla 4 — Ubicación e idioma**
9. ¿Dónde lo guardo? → propone `~/estudio/<slug>/`, `./<slug>/`, y acepta ruta libre.
10. ¿En qué idioma? → default: el idioma en que el usuario está hablando.

**Paso conversacional — Resumen y confirmación.** Una pantalla con todo lo decidido. Solo
con el "sí" se genera.

**Se deriva sin preguntar:** colchón (10-15% de las sesiones, redondeado hacia arriba, mínimo
1), umbrales por defecto, proyección de fechas, tamaño de las evaluaciones.

**No se pregunta, deliberadamente:** estilo de aprendizaje, nivel de detalle, formato de
evaluación. Un default bueno vale más que una pregunta más.

### 4.2 Cascada de fuentes

1. **Oficial** — si el objetivo es `exam` o `tool`, la skill busca la guía oficial (blueprint
   de examen, documentación canónica, syllabus del curso). La extrae y la cita.
2. **Aportada** — links, archivos e imágenes que el usuario entregue. Los links se verifican;
   los archivos se copian a `<ruta>/material/`. Se **incorporan** al temario oficial, no lo
   reemplazan.
3. **Construida** — si no hay ni oficial ni aportada, la skill propone un temario desde su
   conocimiento y lo marca como *construido*. Se valida con el usuario antes de seguir.

**Regla dura:** ningún link se escribe sin verificar que responde (HTTP 200 o equivalente).
Los links verificados llevan fecha de verificación en `PLAN.md`. Si un recurso no se puede
verificar, se omite y se dice.

### 4.3 Diagnóstico según nivel

| Nivel declarado | Acción | Efecto sobre el plan |
|---|---|---|
| Ya trabajo con esto | Diagnóstico completo: 20-25 preguntas sobre todo el temario, ponderadas por área | **Lo más flojo primero.** Siembra *Conceptos a corregir* |
| Sé algo, parcial | Pregunta qué áreas conoce; diagnóstico solo sobre esas | Esas áreas por debilidad; el resto en orden de dependencias |
| Desde cero | **Sin diagnóstico del tema.** Revisión de prerrequisitos | Prerrequisitos faltantes → sesiones 0 al inicio, o aviso si el hueco es grande. Orden de dependencias |

Siempre queda una **línea base escrita** en `diagnostic.md`: resultado por área, o
*"0 sobre el tema; prerrequisitos: X ✓, Y ✗"*.

Si el usuario declara nivel alto y el diagnóstico da por debajo del 50%, la skill lo dice
sin vueltas y propone tratar esas áreas como desde cero.

El diagnóstico pide marcar con `?` lo adivinado, igual que toda evaluación.

### 4.4 Generación

Con temario aprobado, tiempo, nivel, acceso y ruta, la skill:
1. Trocea el temario en sesiones según tamaño de sesión y orden decidido.
2. Inserta sesiones de colchón distribuidas (no todas al final).
3. Marca `is_checkpoint` en las sesiones que cierran bloque o punto de control.
4. Si se declaró una plataforma, busca cursos, los muestra para aprobar y reparte sus clases
   entre las sesiones (§12). Si la plataforma bloquea, sigue sin videos.
5. Proyecta `planned_date` según cadencia desde la fecha de inicio.
6. Genera `PLAN.md`, `sessions/*.md`, `diagnostic.md` si aplica, `material/` si aplica.
7. Registra en `~/.study/plans` y marca `active`.
8. Muestra el calendario resultante.

## 5. Estructura generada

```
<ruta>/
├── PLAN.md
├── diagnostic.md            solo si hubo diagnóstico o revisión de prerrequisitos
├── material/                copias de lo aportado por el usuario
└── sessions/
    ├── session-01-<slug>.md
    ├── session-02-<slug>.md
    └── ...
```

**Carpeta plana.** Reprogramar una sesión es cambiar `planned_date`, nunca mover un archivo.
La agrupación por bloque o semana la da el calendario de `PLAN.md`.

### 5.1 `PLAN.md`

Secciones, en este orden:
1. **Estado actual** (regenerada) — próxima sesión, progreso `N/M`, deriva, colchón restante,
   fin proyectado, último resultado.
2. **Cómo usar esto** — rutina del usuario y los comandos `study-*`.
3. **Calendario** — tabla sesión → fecha prevista → bloque → hito. Agrupada visualmente.
4. **Temario aprobado** — áreas y subtemas con la sesión donde se ven; pesos si existen.
5. **Línea base** — resumen del diagnóstico; link a `diagnostic.md`.
6. **Conceptos a corregir** — tabla con ciclo de vida (§6.5).
7. **Parámetros del protocolo** — tamaños y umbrales editables; la skill los lee de aquí.
8. **Registro de evaluaciones** — una fila por evaluación.
9. **Cierres de bloque** — se van agregando.
10. **Fuentes** — cada una con tipo (oficial/aportada/construida) y fecha de verificación.
11. **Anexo — checklist final** — todos los temas en una lista para el repaso final.

### 5.2 `session-NN-<slug>.md`

Frontmatter (§3.3) y luego:
- **Tema** y **por qué importa** (una o dos líneas, ligadas al objetivo del usuario).
- **Qué estudiar** — checklist.
- **Cómo pensarlo** — analogía o modelo mental que ataque la confusión típica del tema.
- **Lecturas** — tabla recurso · link verificado · tiempo estimado; total al pie.
- **Videos** — si se declaró una plataforma (§12). Opcionales pero al mismo nivel que las
  lecturas: duración propia a la vista, qué cubren y qué no. No suman al tiempo de la sesión.
- **Práctica** — según `practice_level` (§8). Opcional; nunca bloquea.
- **Evaluación** — tipo, umbral, instrucción de marcar `?`, y sección *Resultado* vacía.
- **Apuntes — lo que entendí** — vacío; lo escribe `study-close` con las palabras del usuario.
- **Lo que quedó flojo** — vacío; lo escribe `study-close`.

Sesiones de colchón: `is_buffer: true`, tema "Repaso y recuperación", contenido = repasar
apuntes y conceptos pendientes; sin lecturas nuevas.

### 5.3 `diagnostic.md`

Fecha, nivel declarado, preguntas con respuesta correcta y la del usuario (con `?` si
adivinó), resultado por área, y **la decisión de orden** que tomó la skill y por qué.

## 6. Protocolo de evaluación

### 6.1 Tipos

| Tipo | Cuándo | Sobre qué | Tamaño | Umbral default |
|---|---|---|---|---|
| Diagnóstico | En `study-new` | Según nivel (§4.3) | 20-25 | No aplica |
| De sesión | Al terminar cada sesión de contenido | ~80% tema de hoy + ~20% repaso | ~1 pregunta cada 6-8 min de estudio; min 5, max 15 | 80% |
| De punto de control | En sesiones `is_checkpoint` | Acumulativo desde el punto anterior | 2× la de sesión | 80% |
| Simulacro | Solo `exam` | Todo, imitando el examen real | Igual al examen | 70% el primero; **85% sostenido en dos seguidos** antes de reservar |
| Integradora | Solo sin examen; cierra bloque | Aplicar lo del bloque | Ejercicio práctico si el tema lo permite; si no, 30-40 preguntas | 80% |

Tamaños y umbrales viven en *Parámetros del protocolo* de `PLAN.md`. La skill los lee de ahí.

### 6.2 Formato según objetivo

- `exam`: las preguntas **imitan el formato del examen** (opción múltiple, respuesta múltiple,
  lo que use). Entrenar el formato es parte del objetivo.
- Resto: además de opción múltiple, formatos de comprensión: *explica con tus palabras*,
  *qué está mal en este fragmento*, *escribe el comando/ruta/consulta que…*.

### 6.3 Calidad de las preguntas

1. Cada pregunta se **ancla en una fuente** de la sesión. Sin fuente citable, no se hace.
2. Una sola respuesta defendible (o exactamente N en respuesta múltiple). Distractores que
   alguien con conocimiento incompleto elegiría de verdad.
3. Nunca la misma pregunta dos veces para un concepto: cambia el escenario.
4. Si al corregir una pregunta resulta ambigua o errónea, se **anula y se dice**.

### 6.4 Mecánica de corrección

1. Pedir marcar con `?` lo adivinado. Las acertadas con `?` **cuentan como error** a efectos
   de estudio y se reportan aparte.
2. Entregar primero **puntaje, desglose por área y patrón**. No la lista de errores.
3. Errores **uno por uno, del más simple al más complejo**, esperando respuesta entre cada uno.
   Cada uno con analogía si sirve, link a la fuente, y verificación práctica si el nivel del
   área lo permite.
4. **Verificar antes de afirmar** cualquier dato que no esté en las fuentes de la sesión.
5. **Bajo el umbral no se avanza.** La sesión queda `studied` con `eval_passed: false`.
   `study-next` ofrece repaso de lo fallado y **re-evaluación corta con preguntas nuevas**
   solo sobre eso. Aprobada, la sesión pasa a `evaluated`.

### 6.5 Conceptos a corregir — ciclo de vida

```
pendiente → explicado → confirmado×1 → consolidado
```

- Nace **pendiente** al fallar (o al acertar con `?`). Pasa a **explicado** al corregirse.
- Se re-pregunta en **toda** evaluación siguiente dentro de la cuota de repaso.
- Correcta sin `?` → sube un escalón. Con `?` o incorrecta → vuelve a **explicado**.
- **Dos correctas seguidas** → consolidado. Sale de la cuota.
- La cuota de repaso se llena: no consolidados primero; el resto con temas de sesiones
  anteriores al azar (repetición espaciada implícita).

Cada entrada guarda: concepto, error cometido, sesión donde se enseña, estado, fechas.

### 6.6 Qué escribe `study-eval`

En una sola operación: frontmatter (`eval_score` del último intento, `eval_passed`, `eval_date`,
`eval_attempts` incrementado), una línea por intento en la región *Resultado*, **la región `weak`
cuando no se llega al umbral**, fila en *Registro* de `PLAN.md` (tipo `<eval_type> re-eval` si es
una re-evaluación), altas y cambios en *Conceptos a corregir*, y *Estado actual*. Detalle en §13.

## 7. Ciclo de sesiones y recuperación

### 7.1 `study-next`

1. Resuelve plan activo (§3.2).
2. Lee frontmatter de todas las sesiones; toma la **primera no `closed`**. No usa la fecha de
   hoy para elegir.
3. **Mide deriva**: `planned_date` de esa sesión vs hoy. Atraso → §7.5. Adelanto → lo dice y
   ofrece adelantar.
4. Si la sesión es de colchón y no hay atraso → ofrece saltarla o usarla de repaso. El
   colchón no se gasta solo.
5. Según `status`:
   - `pending` → presenta la sesión completa; marca `studied`, `actual_date` = hoy.
   - `studied`, sin evaluar → ofrece evaluar (*"esto ya lo abriste el <fecha>"*).
   - `studied`, `eval_passed: false` → ofrece repaso + re-evaluación corta.
   - `evaluated` → ofrece cerrar.
   - Si `eval_type: none` (sesiones de colchón), no hay evaluación: de `studied` se ofrece
     cerrar directamente.
6. Argumento opcional `<slug>` para operar un plan que no es el activo.

### 7.2 `study-eval`

Sin argumento: evalúa la sesión en curso con el tipo que indica su frontmatter. Con
argumento fuerza tipo: `mock`, `checkpoint`, `integrative`, `diagnostic`. Sigue §6.

### 7.3 `study-close`

Sobre la sesión en `evaluated`:
1. Pide al usuario **explicar con sus palabras las 2-3 ideas centrales**. Con eso escribe
   *Apuntes — lo que entendí*. Es el paso Feynman y, para áreas sin entorno, la práctica.
2. Escribe *Lo que quedó flojo* con los errores de la evaluación más lo que el usuario agregue.
3. Marca `closed`.
4. Si `is_checkpoint`: escribe el **cierre de bloque** en `PLAN.md` — cubierto, resultado,
   conceptos consolidados y pendientes, deriva — y deja el texto listo para copiar si el hito
   era externo. No publica nada.
5. Regenera *Estado actual*.

### 7.4 `study-status`

Solo lectura salvo cambio de plan activo. Muestra: plan activo, próxima sesión, progreso,
deriva, colchón restante, conceptos pendientes, últimas evaluaciones, **fin proyectado al
ritmo real**. `study-status all` lista planes y permite cambiar `active`.
`study-status replan` → §7.6.

### 7.5 Recuperación por atraso

Detectada en `study-next`. Política según horizonte:

**`flexible` u `open`:** reproyecta fechas y lo dice en una línea. Los hitos externos fijos no
se mueven; avisa qué se habrá cubierto para esa fecha.

**`fixed`:** propone en orden, mostrando el calendario resultante, y aplica solo con aprobación:
1. **Consumir colchón** mientras quede.
2. **Doblar** — dos sesiones en una fecha, solo si ambas son livianas (por tiempo de lectura).
3. **Recortar** — fusionar o adelgazar las más livianas. Muestra qué se pierde antes de tocar.

Si no alcanza: lo dice y ofrece subir cadencia o mover la fecha.

### 7.6 Replan

`study-status replan`: vuelve a preguntar solo cadencia y horizonte, recalcula proyección,
y si el fin es `fixed` y no alcanza, entra en §7.5. **No regenera contenido**: mueve fechas
y, si hace falta, recorta.

### 7.7 Tabla de escritura

| Comando | Frontmatter | `PLAN.md` | `~/.study/` |
|---|---|---|---|
| `study-new` | crea | crea | `plans`, `active` |
| `study-next` | `status`, `actual_date`, `planned_date` si reproyecta | Estado actual; Calendario si reproyecta | — |
| `study-eval` | `eval_*` | Registro; Conceptos a corregir; Estado actual | — |
| `study-close` | `status: closed` | Estado actual; Cierres de bloque | — |
| `study-status` | — | Calendario si replan | `active` si cambia |

## 8. Práctica — tres niveles

Elegido por **área** según acceso declarado, no por tema. Opcional por sesión: la sesión
está completa sin ella y no afecta el umbral.

| Nivel | Cuándo | Qué genera |
|---|---|---|
| `live` | Acceso real al área | Ejercicios contra el entorno del usuario, comentados para que la salida enseñe. **Solo lectura** si el entorno es compartido o productivo; libres si es un proyecto local descartable del alumno. Deben correr tal cual (§13) |
| `sandbox` | Sin acceso, pero existe alternativa gratuita o local **verificable** | Free tier, playground oficial, emulador local, consola online |
| `none` | Nada que tocar, o tema conceptual | *Explícamelo con tus palabras* + ejemplos trabajados con salida real tomada de la fuente oficial |

Si un comando `live` falla por permisos, la skill lo trata como **dato**: lo anota en la
sesión, baja el área a `sandbox` o `none`, y no vuelve a proponer acceso a eso. Si un
comando tiene costo (APIs que cobran por request), se advierte antes de sugerirlo.

## 9. Reglas transversales

1. **Nunca inventar** URLs, datos de examen, precios ni nombres de servicios. Verificar o decir
   que no se pudo verificar.
2. **Errores uno por uno**, del más simple al más complejo, esperando respuesta.
3. **Apuntes con las palabras del usuario**, no resúmenes genéricos.
4. **Estado en frontmatter**; `PLAN.md` se regenera, no se edita a mano.
5. **Nada se publica** fuera del disco local.
6. **Degradación**: si `AskUserQuestion` no está disponible, preguntar en texto plano con las
   mismas opciones.
7. **Idioma**: estructura en inglés, contenido en el del usuario, `SKILL.md` en inglés.

## 10. Fuera de alcance (deliberado)

Pausar o archivar planes · sincronización entre máquinas · notificaciones o recordatorios ·
publicación en Jira o Slack · soporte para Cursor/Codex · varios usuarios sobre un mismo plan ·
lo excluido en §12.8 (YouTube, refresco de videos, preferencia de aprendizaje).
Se agregan si hacen falta, no antes.

## 11. Distribución

- El repo trae `install.sh`, que copia (o enlaza con `--link`) las seis carpetas `study-*` en
  `~/.claude/skills/`. `INSTALL.md` explica los mismos pasos para que un agente los siga.
- Solo se instala en `~/.claude/skills/` (Claude Code). No aplica a `~/.agents/skills/`.

## 12. Videos por sesión

> Aprobado en conversación el 2026-09-23. Se construye junto con la iteración 2.

### 12.1 Propósito

Que cada sesión, además de sus lecturas oficiales, indique **qué curso y qué clase en video**
sirven para ese tema, elegidos comparando el tema de la sesión con el contenido de cada clase.

### 12.2 Decisiones

| Decisión | Valor |
|---|---|
| Tiempo | La estimación de la sesión es **solo de lecturas**. Los videos llevan su propia duración, a la vista |
| Peso | Opcionales pero **no descartables**: para algunas personas el audiovisual es lo principal. Se curan con el mismo cuidado que las lecturas y se muestran al mismo nivel |
| Momento | Se buscan **al crear el plan** (`study-new`) y quedan escritos en cada sesión |
| Plataformas v1 | **Platzi** (consulta automática) + **pegado manual** del índice de cualquier otra |
| Preferencia de aprendizaje | No se pregunta: todas las sesiones muestran videos y lecturas al mismo nivel |

### 12.3 Entrevista

Pregunta 7 de la Pantalla 3 (§4.1): *¿Tienes acceso a alguna plataforma de cursos?* → Platzi ·
otra (pegas el índice) · ninguna. Selección múltiple. "Ninguna" no busca nada.

### 12.4 Flujo con Platzi

Después de aprobar el temario y trocear las sesiones:

1. **Catálogo.** Bajar `https://platzi.com/sitemap-cursos.xml` (~1.600 cursos). Caché en
   `~/.study/cache/platzi/` con fecha; se reutiliza si tiene menos de 7 días.
2. **Candidatos.** El modelo elige cursos del catálogo por el tema del plan y abre la página de
   los mejores (título, descripción, nivel) para decidir. **Se muestran al usuario para aprobar**,
   igual que el temario: un curso **principal** y como mucho **dos complementarios** que tapen huecos.
3. **Índices.** Una request por curso aprobado. La página del curso trae cada clase con número,
   título real y duración (enlace `href="/cursos/<curso>/<clase>/"` con texto `N Título MM:SS min`).
   Se guarda en `<plan>/material/videos-index.json`: solo número, título, duración, URL y curso.
4. **Reparto.** El modelo asigna clases a cada sesión de contenido según su checklist. Si un título
   no alcanza para decidir, lee el **resumen escrito** de esa clase (público, debajo del video) y
   **no lo guarda**. Se prefiere el curso principal; los complementarios solo tapan huecos.
5. **Cobertura honesta.** Cada sesión dice qué cubren los videos y qué no. Si ningún video sirve
   para un tema, lo dice en vez de rellenar con uno parecido.

Presupuesto: entre 5 y 20 requests a Platzi por plan. Nunca bajar las ~32.000 clases.

Hechos verificados el 2026-09-23 que condicionan el diseño:
- El `meta description` de una página de clase es **el del curso**, no el de la clase. Lo
  específico de la clase es el título y el resumen del cuerpo de la página.
- Los slugs de las URLs **no coinciden** con el título real (se renombran clases sin cambiar la
  URL). El match se hace sobre títulos reales, nunca filtrando slugs por palabra clave.

### 12.5 Pegado manual (cualquier otra plataforma)

El usuario copia el índice que muestra la página de su curso (Udemy, Coursera, un curso interno)
y lo pega. El modelo lo interpreta con tolerancia (secciones, clases, duraciones y URLs si vienen)
y lo reparte igual que en 12.4, paso 4. No se consulta nada afuera. Se guarda en el mismo
`videos-index.json` con un campo `platform` que indica el origen.

### 12.6 Sección Videos en la sesión

- Encabezado de la sesión: `Lectura ~N min · Videos ~M min (opcional)`.
- Frontmatter: `video_minutes: M` (suma de duraciones; no entra en ningún cálculo de tiempo).
- Tabla: clase (número + título), curso, duración, link.
- Línea de cobertura: *Cubren: … · No cubren: … → quédate con la lectura*.
- `study-next` presenta los videos **con el mismo peso** que las lecturas, no como nota al pie.
- Las sesiones de colchón no llevan videos nuevos.

### 12.7 Reglas

1. **Nunca copiar contenido de la plataforma.** Solo título, duración y URL. Los resúmenes se leen
   para decidir y no se escriben en ningún archivo. Los términos de Platzi no mencionan bots ni
   IA, pero prohíben copiar o reproducir su contenido en todo o en parte.
2. **Identificarse honestamente.** User-Agent propio de la skill; nunca disfrazado de navegador.
3. **Pocas requests y caché.** Pausa de 2-3 s entre requests.
4. **Si la plataforma bloquea, el plan sale igual.** Platzi usa Cloudflare Bot Management, que da
   403 intermitentes. Reintentar dos veces con pausa; si sigue bloqueado, generar el plan sin
   videos y anotarlo en `PLAN.md`. Pedir después "agrega los videos" reintenta solo esa búsqueda;
   no es un comando de refresco general.
5. **Las URLs salen de la página del curso consultada ese mismo día**: no requieren otra
   verificación por clase.
6. **Los videos envejecen.** La documentación oficial sigue siendo la fuente de verdad; si un
   video contradice la lectura, manda la lectura y la sesión lo advierte.

### 12.8 Qué no hace (deliberado)

YouTube u otras APIs de video (exigen API key por persona; queda para después) · comando de
refresco de videos · preguntar la preferencia de aprendizaje · reproducir el video · guardar
resúmenes o descripciones de las plataformas.

### 12.9 Archivos que se tocan

`study-shared/scripts/platzi.py` (catálogo con caché + índice de un curso, solo librería
estándar) · `study-shared/references/videos.md` (nueva) · `study-shared/templates/session.md`
(sección Videos, `video_minutes`) · `study-shared/references/frontmatter.md` ·
`study-shared/references/interview.md` · `study-new/SKILL.md` (pregunta y paso de búsqueda) ·
`study-next/SKILL.md` (presentación con el mismo peso que las lecturas).

## 13. Iteración 2 — decisiones de protocolo, práctica y calidad

> Tomadas el 2026-09-23 a partir de las pruebas de la iteración 1 y del uso real de un plan
> de AWS CLF-C02. El detalle operativo vive en `references/`; aquí queda el porqué.

### 13.1 Evaluación

| Tema | Decisión | Por qué |
|---|---|---|
| Re-evaluación | 2 preguntas por concepto flojo (mín 4, máx 10), umbral `threshold_session` | "Corta" no era un tamaño; cada sesión lo resolvía distinto |
| Momento de la re-eval | Recomendada al inicio de la sesión siguiente, no justo después del repaso | Justo después mide memoria de corto plazo |
| Historial de intentos | `eval_score` = último; `eval_attempts` = cantidad; una línea por intento en *Resultado*; el log guarda todos | La re-eval pisaba el primer puntaje |
| Escalones de concepto | Máximo uno por evaluación | Acertar dos veces en la misma evaluación no es retención |
| Acertadas con `?` | Correctas para el puntaje y el umbral; error para el seguimiento de conceptos; todo `?` genera fila | Era ambiguo y cada sesión lo contaba distinto |
| Región `weak` | La escribe `study-eval` al reprobar; `study-close` la reescribe al cerrar | `study-next` repasaba una región que nadie llenaba |
| Posición de la correcta | La sortea `study_state.py answer-key` antes de escribir las opciones: sin letra por encima de su parte justa + 1 y nunca tres seguidas iguales | En una evaluación real 7 de 8 respuestas fueron B y el usuario empezó a responder el patrón |
| Entrega | `--clicks` (`AskUserQuestion`: tandas de 3 + "¿cuáles adivinaste?") o `--text` (todo en un mensaje). Por defecto clics hasta 12 preguntas y texto por encima; las de 5+ opciones y las abiertas siempre en texto | Clics quitan fricción en evaluaciones cortas; en simulacros de 65 serían 22 diálogos sin poder volver atrás, y el examen real deja revisar antes de entregar |

### 13.2 Práctica

- `live` distingue **entorno compartido o productivo** (solo lectura) de **proyecto local
  descartable** (se puede modificar): la regla vieja volvía inútil la práctica de un framework.
- **Los comandos corren tal cual.** Se resuelve la identidad antes, y nunca hay placeholders tipo
  `<tu-usuario>` en un bloque ejecutable: zsh los toma como redirección y el botón Run del
  desktop app falla.
- La entrevista pregunta **cómo se autentica** el alumno en entornos remotos (usuario IAM o rol
  de Identity Center): los comandos "sobre tu usuario" no aplican a quien entra por un rol.

### 13.3 Calidad del contenido que genera `study-new`

- **Cada afirmación del checklist y de la analogía se respalda en una lectura de la sesión.** Un
  200 de `verify_links.py` prueba que la página existe, no lo que dice. Caso real: una sesión
  afirmaba que cambiar el plan de soporte era tarea exclusiva del root, y eso ya no figura en la
  lista oficial.
- **Cada ítem del checklist tiene al menos una lectura** que lo cubra: dos de tres errores de una
  evaluación real cayeron en ítems sin lectura.
- **Doc localizada** en el idioma del plan cuando existe, con anchor a la sección exacta.
- **Hitos contra calendario:** `study_state.py check` valida que cada hito externo (`milestones:`)
  tenga un checkpoint antes. Corre al generar el plan y tras cada reproyección, porque reproyectar
  puede empujar un checkpoint más allá de su hito.
- Versión de examen retirada → se construye contra la vigente y se confirma con el usuario.
  Versión pedida que no es la última → se construye para la pedida y se avisa. Sin cantidad o
  pesos oficiales → se eligen y se declaran como elección del plan.

### 13.4 Mecánica

- **Fechas de `python3 study_state.py today`**, nunca de `date`: respeta `STUDY_TODAY` en pruebas
  y evita errores de zona horaria.
- `check` detecta placeholders propios sin confundirlos con Blade/Jinja, fechas faltantes, hitos
  sin checkpoint y colchones con evaluación.
- `verify_links.py` sigue redirecciones (incluida la 308), reintenta ante 429 y distingue
  `REDIRECT`, `RATE-LIMITED`, `BLOCKED` y `SPA?` de `BAD`: antes daba por buenos redirects a otra
  página y rutas inventadas de sitios SPA.
- Plantillas localizadas: los textos fijos salen de `references/labels.md` (es/en/pt) en vez de
  traducirse a mano en cada plan.
- En `study-next`: primero se marca la sesión y después se responde; no se marca `studied` una
  sesión incompleta; calentamiento opcional tras 7 días sin actividad (`days_since_last_activity`,
  que toma la fecha más reciente entre apertura, evaluación y cierre: una sesión puede quedar abierta
  varios días); no se reverifican links.

## 14. Referencia

El plan real de AWS CLF-C02 que originó esta familia es el ejemplo de referencia de
*calidad de contenido* (analogías, comandos comentados, lecturas verificadas, protocolo).
**No** es referencia de estructura: usa carpetas por semana y fechas en los nombres, que este
diseño reemplaza por sesiones planas con estado en frontmatter.
