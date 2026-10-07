# study-skills

*[Read in English](README.md)*

Skills de **Claude Code** para armar y seguir un plan de estudio sobre cualquier tema:
una certificación, un framework, un libro o un curso. Sirven para cualquier duración y cadencia.

Claude arma el temario a partir de fuentes oficiales verificadas y lo divide en sesiones con
lecturas, una analogía, práctica y videos opcionales. En cada sesión te evalúa, corrige tus
errores uno por uno y guarda tus apuntes con tus palabras. El plan es una **cola de sesiones, no un
calendario**: si faltas una semana no se rompe nada. Se reproyectan las fechas y sigues donde
te quedaste.

> **¿Eres un agente y te pidieron instalar esto?** Sigue [INSTALL.md](INSTALL.md) (en inglés).

## Instalación

Requisitos: Claude Code y Python 3.9 o más nuevo (`python3`). No hay que instalar nada más.

```bash
git clone https://github.com/kleyver14/study-skills.git study-skills
cd study-skills
./install.sh            # copia las skills en ~/.claude/skills/
# ./install.sh --link   # o enlaza, para que `git pull` las actualice
```

Después abre una sesión nueva de Claude Code. También puedes pasarle el link del repo a tu agente
y pedirle: *"instala estas skills"*.

## Uso

| Comando | Qué hace | También se activa con |
|---|---|---|
| `/study-new` | Te entrevista y genera el plan: `PLAN.md` y un archivo por sesión | "quiero aprender X", "tengo que certificarme en Y" |
| `/study-next` | Abre la próxima sesión pendiente y te avisa si vas atrasado | "qué estudio hoy", "sigamos con el plan" |
| `/study-eval` | Te evalúa sobre la sesión actual, o te toma un simulacro | "evalúame", "hazme la evaluación", "simulacro" |
| `/study-close` | Te pide que expliques con tus palabras lo aprendido y cierra la sesión | "listo por hoy", "cerremos la sesión" |
| `/study-status` | Muestra cómo vas, cuándo terminarías a tu ritmo real y cambia de plan activo | "cómo voy", "me adelantaron el examen" |

El ciclo de cada sesión es `/study-next` → estudiar → `/study-eval` → `/study-close`.

### Cómo respondes las evaluaciones

| Modo | Cómo se ve | Por defecto |
|---|---|---|
| `--clicks` | Diálogos donde eliges las opciones con un clic (tandas de 3 preguntas más "¿cuáles adivinaste?"), incluso con selección múltiple | Evaluaciones de 12 preguntas o menos |
| `--text` | Todas las preguntas en un mensaje; respondes `1. A`, `2. C?` (el `?` marca lo que adivinaste) | Simulacros y diagnósticos, para revisar todo antes de entregar como en el examen real |

Ejemplos: `/study-eval --text`, `/study-eval mock --clicks`. También puedes decirlo con
palabras: "hazme la evaluación con clics". Las preguntas de 5 o más opciones y las abiertas van
siempre en texto, porque el diálogo muestra hasta 4 opciones. En los dos modos, la posición de la
respuesta correcta se sortea.

### Idiomas

- **Los archivos** se escriben en el idioma en que lo pides: `/study-new i want to learn laravel
  12` genera el plan en inglés, y "quiero estudiar AWS", en español. Si lo dices explícitamente,
  gana ("los archivos en inglés"). El resumen antes de generar lo muestra, así que ahí puedes
  cambiarlo.
- **La conversación** sigue el idioma de tu último mensaje, sea cual sea el del plan. Puedes
  estudiar para un examen en inglés conversando en español.
- Las preguntas de evaluación vienen en el idioma del plan, porque salen de las lecturas; puedes
  pedir otro idioma para una evaluación puntual. Tus apuntes quedan con tus palabras, sin traducir.
- Los textos fijos existen en español neutro, inglés y portugués. Para otro idioma, Claude ofrece
  textos en inglés o traducirlos una vez para todo el plan.

### La entrevista de `/study-new`

Son cuatro pantallas cortas:

1. **Objetivo y fuentes.** Qué quieres estudiar y qué material tienes. Claude busca las fuentes
   oficiales y te propone un temario, y no genera nada hasta que lo apruebes.
2. **Tiempo y nivel.**
   - Fecha límite: exacta, aproximada ("unos 3 meses") o ninguna.
   - Cuántos días por semana y cuántos minutos por sesión.
   - Tu nivel actual. Según eso te toma un diagnóstico o revisa los prerrequisitos.
3. **Práctica, videos y seguimiento.**
   - Si tienes acceso real, un entorno de prueba o nada para practicar. Se elige por área.
   - Si usas una plataforma de cursos: Platzi, o cualquier otra pegando el índice del curso.
   - Si reportas el avance a alguien, por ejemplo en 1:1.
4. **Ubicación.** Dónde guardar el plan.

### Qué queda en disco

```
<carpeta que elijas>/
├── PLAN.md                 configuración, calendario, conceptos pendientes, registro de evaluaciones
├── diagnostic.md           punto de partida
└── sessions/
    ├── session-01-<tema>.md
    └── …
~/.study/                   registro de tus planes y cuál está activo
```

Todo es Markdown local: puedes leerlo, versionarlo o editarlo. El estado de cada sesión vive en su
frontmatter, y las secciones de `PLAN.md` entre marcadores `<!-- study:… -->` las regenera la
skill, así que no conviene editarlas a mano. Puedes tener varios planes a la vez y cambiar entre
ellos con `/study-status all`.

## Opcional: el panel de estudio (mod)

`mods/study-companion` agrega a Claude Code (terminal y app de escritorio) un panel con el estado
de tu plan activo: progreso, próxima sesión, atraso, fin proyectado, buffer, conceptos por
corregir y última evaluación, más botones para el siguiente paso (*Abrir S05*, *Evaluar* o
*Cerrar sesión*, según dónde estés) y el estado completo.

- `/study-panel` lo abre y responde desde `study_state.py`, sin llamar al modelo.
- El primer comando de estudio de la sesión lo abre solo, una vez; si lo cierras, queda cerrado.
- Una línea de estado como `📚 mi-plan · S05 · 4/28 · 7 atrás` aparece solo en sesiones de
  estudio: después de usar una skill `study-*`, de `/study-panel`, o si la sesión se abre en la
  carpeta del plan.
- Si llevas 7 días o más sin estudiar, una sesión de estudio te lo recuerda al iniciar.

Se instala desde la carpeta del repo (es un plugin de Claude Code; las skills funcionan sin él):

```bash
claude plugin marketplace add "$PWD"
claude plugin install study-companion@study-skills
```

Las sesiones nuevas lo cargan. Los mods son una función en acceso anticipado de Claude Code, así
que su API puede cambiar.

## Principios

- **Nada inventado.** Todo link pasa por `verify_links.py` antes de escribirse, y cada afirmación
  de una sesión está respaldada por una lectura.
- **Nada se publica.** Las skills no usan Jira, Slack ni ningún servicio externo. Los resúmenes
  de cierre de bloque quedan listos para que los copies donde quieras.
- **La práctica corre tal cual.** Los comandos no llevan `<placeholders>` y respetan el nivel de
  acceso que declaraste. Si algo falla por permisos, se baja el nivel de esa área.
- **Evaluaciones con criterio.** Marcas lo que adivinaste, y la posición de la respuesta
  correcta se sortea, así que no hay patrón que aprender. Los errores se corrigen uno por uno, y
  un concepto queda "pendiente" hasta que lo aciertes en evaluaciones distintas.
- **Videos con respeto.** De Platzi solo se guardan título, duración y URL, nunca el contenido
  (lo exigen sus términos de uso).

## Estructura del repo

```
skills/
├── study-new/ study-next/ study-eval/ study-close/ study-status/   un SKILL.md por comando
└── study-shared/
    ├── DESIGN.md       especificación y el porqué de cada decisión
    ├── scripts/        study_state.py (estado), verify_links.py, platzi.py (solo stdlib)
    ├── templates/      plan, sesión y diagnóstico
    └── references/     protocolo de evaluación, recuperación, práctica, videos, idioma, textos fijos
mods/study-companion/   panel, línea de estado y /study-panel opcionales (plugin de Claude Code)
.claude-plugin/         marketplace que lista el mod
tests/                  unittest, sin red
install.sh
```

Para correr los tests: `cd tests && python3 -m unittest test_study_state test_verify_links test_platzi`.

## Limitaciones

- Funciona solo en Claude Code, porque usa `AskUserQuestion`. En otros agentes no está probado.
- Para videos, v1 soporta Platzi y un índice pegado a mano. Platzi a veces bloquea las consultas
  automáticas; en ese caso el plan se genera sin videos y lo avisa.
- No hay recordatorios ni sincronización entre máquinas. Si quieres tus planes en varias
  computadoras, versiona la carpeta del plan con git.

## Desinstalar

```bash
./install.sh --uninstall   # quita las skills; tus planes y ~/.study quedan intactos
claude plugin uninstall study-companion@study-skills   # el panel, si lo instalaste
```

Cambios por versión: [CHANGELOG.md](CHANGELOG.md).

## Licencia

[MIT](LICENSE)
