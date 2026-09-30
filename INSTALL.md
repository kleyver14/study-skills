# Instalación — instrucciones para el agente

> Si eres un agente (Claude Code) y te pasaron este repo para instalarlo, sigue estos pasos en
> orden. Si eres una persona, el [README](README.md) tiene lo mismo más corto.

## Qué se instala

Seis carpetas de skills en `~/.claude/skills/`:
`study-shared`, `study-new`, `study-next`, `study-eval`, `study-close`, `study-status`.
No se instalan dependencias ni paquetes, no se tocan configuraciones y nada sale del disco local.
Los planes del usuario viven donde elija, y el registro de planes en `~/.study/`.

## Requisitos (verifícalos antes de instalar)

1. **Claude Code** (terminal, app de escritorio o web con repo local). Las skills usan la
   herramienta `AskUserQuestion`: no están pensadas para Cursor, Codex ni `~/.agents/skills/`.
2. **Python 3.9 o más nuevo** como `python3`, solo biblioteca estándar:
   ```bash
   python3 --version
   ```
3. **bash** para `install.sh` (macOS y Linux lo traen; en Windows, usar WSL o Git Bash).

Si falta alguno, díselo al usuario y no sigas.

## Pasos

1. Clonar el repo, si todavía no está en disco (el usuario elige la carpeta):
   ```bash
   git clone <url-del-repo> study-skills
   cd study-skills
   ```
2. Revisar si ya hay una versión instalada:
   ```bash
   ls -d ~/.claude/skills/study-* 2>/dev/null
   ```
   Si aparece algo, **pregúntale al usuario** antes de reemplazarlo. Con su aprobación, usa
   `--force`: el script mueve la versión anterior a `~/.study/backup/skills-<fecha>/`, no la borra.
3. Instalar. Elige el modo con el usuario:
   - **Copia** (por defecto): queda independiente del repo.
     ```bash
     ./install.sh
     ```
   - **Enlace** (`--link`): symlinks al repo; un `git pull` actualiza las skills. Útil si el usuario
     va a modificarlas o seguir las actualizaciones. No mover ni borrar el repo después.
     ```bash
     ./install.sh --link
     ```
4. Verificar. El script ya lo hace al final; para repetirlo:
   ```bash
   ./install.sh --check
   ```
   Tiene que listar las seis skills con `ok` y terminar con `study_state.py runs: ok`.
5. Opcional, recomendado si se instaló con `--link` o se modificó algo:
   ```bash
   cd tests && python3 -m unittest test_study_state test_verify_links test_platzi
   ```
   Corre sin red (usa un servidor HTTP local y fixtures sintéticas).
6. Dile al usuario, en su idioma:
   - que **abra una sesión nueva de Claude Code** (las skills se cargan al iniciar) y empiece con
     `/study-new`, o simplemente con "quiero armar un plan de estudio para …";
   - los cinco comandos y el ciclo `/study-next` → estudiar → `/study-eval` → `/study-close`
     (tabla *Uso* del README);
   - **cómo se responden las evaluaciones**: `/study-eval --clicks` para elegir opciones con un
     clic, `/study-eval --text` para todas las preguntas en un mensaje. Sin flag: clics hasta 12
     preguntas, texto en simulacros y diagnósticos. También se puede pedir con palabras.

## Actualizar

- Instalado con `--link`: `git pull` en el repo, nada más.
- Instalado por copia: `git pull` y después `./install.sh --force`.

Los planes existentes no se modifican al actualizar.

## Desinstalar

```bash
./install.sh --uninstall
```

Quita solo las seis carpetas `study-*`. **No** toca los planes del usuario ni `~/.study/`; si el
usuario también quiere borrar eso, que lo haga él.

## Instalación manual (sin `install.sh`)

```bash
mkdir -p ~/.claude/skills
cp -R skills/study-* ~/.claude/skills/
python3 ~/.claude/skills/study-shared/scripts/study_state.py today
```

El último comando tiene que imprimir la fecha de hoy (`YYYY-MM-DD`).

## Variables de entorno (opcionales)

| Variable | Para qué |
|---|---|
| `CLAUDE_SKILLS_DIR` | Instalar en otra carpeta que no sea `~/.claude/skills` (`install.sh`) |
| `STUDY_HOME` | Usar otra carpeta en lugar de `~/.study` para el registro y la caché |
| `STUDY_TODAY` | Fijar "hoy" en `YYYY-MM-DD` (pruebas) |
