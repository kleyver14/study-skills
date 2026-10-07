import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { StudyEval, StudyNext, StudySummary } from '../types'

const PANE = 'study'
const REFRESH_MS = 10 * 60 * 1000
const IDLE_DAYS = 7
const summary = atom({ plugin: 'study-companion', key: 'summary' } as const, null)
const problem = atom({ plugin: 'study-companion', key: 'problem' } as const, null)
// Set once the session studies: a study-* skill ran, /study-today, or it opened in the plan folder.
const isActive = atom({ plugin: 'study-companion', key: 'isActive' } as const, false)

type Words = typeof WORDS.en

const WORDS = {
  en: {
    title: 'Study',
    loading: 'Reading the active plan…',
    next: 'Next',
    noNext: 'Plan finished',
    planned: 'planned',
    onTrack: 'On track',
    behind: (n: number) => `${n} session${n === 1 ? '' : 's'} behind`,
    ahead: (n: number) => `${n} session${n === 1 ? '' : 's'} ahead`,
    behindShort: 'behind',
    buffer: 'Buffer',
    end: 'End',
    plan: 'plan',
    atPace: 'at your pace',
    concepts: 'Concepts to fix',
    lastEval: 'Last evaluation',
    passed: 'passed',
    failed: 'not passed',
    none: 'none yet',
    idle: (n: number) => `${n} days without studying`,
    status: { pending: 'pending', studied: 'open', evaluated: 'evaluated', closed: 'closed' } as Record<string, string>,
    open: (n: string) => `Open ${n}`,
    evaluate: 'Evaluate',
    close: 'Close session',
    details: 'Full status',
    refresh: 'Refresh',
    hide: 'Close pane',
    running: (command: string) => `Running /${command}…`,
    opened: 'Study pane opened.',
    nudge: (days: number, slug: string) => `${days} days since you last studied ${slug} · /study-next`,
  },
  es: {
    title: 'Estudio',
    loading: 'Leyendo el plan activo…',
    next: 'Próxima',
    noNext: 'Plan terminado',
    planned: 'prevista',
    onTrack: 'Al día',
    behind: (n: number) => `${n} ${n === 1 ? 'sesión' : 'sesiones'} de atraso`,
    ahead: (n: number) => `${n} ${n === 1 ? 'sesión' : 'sesiones'} adelantado`,
    behindShort: 'atrás',
    buffer: 'Buffer',
    end: 'Fin',
    plan: 'plan',
    atPace: 'a tu ritmo',
    concepts: 'Conceptos por corregir',
    lastEval: 'Última evaluación',
    passed: 'aprobada',
    failed: 'no aprobada',
    none: 'ninguna aún',
    idle: (n: number) => `${n} días sin estudiar`,
    status: { pending: 'pendiente', studied: 'abierta', evaluated: 'evaluada', closed: 'cerrada' } as Record<string, string>,
    open: (n: string) => `Abrir ${n}`,
    evaluate: 'Evaluar',
    close: 'Cerrar sesión',
    details: 'Estado completo',
    refresh: 'Actualizar',
    hide: 'Cerrar panel',
    running: (command: string) => `Ejecutando /${command}…`,
    opened: 'Panel de estudio abierto.',
    nudge: (days: number, slug: string) => `Hace ${days} días que no estudias ${slug} · /study-next`,
  },
}

const words = (language: string): Words => (language === 'es' ? WORDS.es : WORDS.en)

const pad = (n: number) => `S${String(n).padStart(2, '0')}`

// Concept rows whose status cell is anything but consolidated.
export function countPending(plan: string): number {
  const start = plan.indexOf('<!-- study:concepts:begin -->')
  const end = plan.indexOf('<!-- study:concepts:end -->')
  if (start === -1 || end === -1) return 0
  const states = ['pending', 'explained', 'confirmed', 'consolidated']
  return plan
    .slice(start, end)
    .split('\n')
    .map(line => line.split('|').map(cell => cell.trim()))
    .map(cells => cells.find(cell => states.some(s => cell.startsWith(s))))
    .filter(state => state !== undefined && !state.startsWith('consolidated')).length
}

type RawStatus = {
  total: number
  closed: number
  next: { session: number; title: string; status: string; planned_date: string | null } | null
  behind_sessions: number
  ahead_sessions: number
  buffer_total: number
  buffer_left: number
  planned_end: string | null
  projected_end: string | null
  last_eval: StudyEval | null
  days_since_last_activity: number | null
  plan: { slug: string; topic: string; language: string }
}

export function toSummary(raw: RawStatus, pendingConcepts: number): StudySummary {
  const next: StudyNext | null = raw.next
    ? { session: raw.next.session, title: raw.next.title, status: raw.next.status, plannedDate: raw.next.planned_date }
    : null
  return {
    slug: raw.plan.slug,
    topic: raw.plan.topic,
    language: raw.plan.language,
    closed: raw.closed,
    total: raw.total,
    next,
    behind: raw.behind_sessions,
    ahead: raw.ahead_sessions,
    bufferLeft: raw.buffer_left,
    bufferTotal: raw.buffer_total,
    plannedEnd: raw.planned_end,
    projectedEnd: raw.projected_end,
    lastEval: raw.last_eval,
    daysIdle: raw.days_since_last_activity,
    pendingConcepts,
  }
}

async function resolvePlan($: EngineInterface): Promise<{ script: string; path: string } | null> {
  const home = await $.env.get('HOME')
  const script = `${home}/.claude/skills/study-shared/scripts/study_state.py`
  const resolved = await $.process.run(['python3', script, 'registry', 'resolve'])
  return resolved.exitCode === 0 ? { script, path: resolved.stdout.trim() } : null
}

async function load($: EngineInterface): Promise<StudySummary | string> {
  const plan = await resolvePlan($)
  if (!plan) return 'No active study plan: /study-new'
  const { script, path } = plan
  const status = await $.process.run(['python3', script, 'status', path])
  if (status.exitCode !== 0) return `study_state.py failed: ${status.stderr.trim().slice(0, 160)}`
  const planText = await $.fs.read(`${path}/PLAN.md`).then(text => (typeof text === 'string' ? text : ''), () => '')
  return toSummary(JSON.parse(status.stdout) as RawStatus, countPending(planText))
}

export function statusLine(s: StudySummary): string {
  const t = words(s.language)
  const at = s.next ? pad(s.next.session) : t.noNext
  const drift = s.behind > 0 ? ` · ${s.behind} ${t.behindShort}` : ''
  return `📚 ${s.slug} · ${at} · ${s.closed}/${s.total}${drift}`
}

export function summaryText(s: StudySummary): string {
  const t = words(s.language)
  const lines = [`**${s.topic}** · ${s.closed}/${s.total}`]
  if (s.next) {
    const state = t.status[s.next.status] ?? s.next.status
    lines.push(`${t.next}: ${pad(s.next.session)} · ${s.next.title} (${state})`)
  }
  lines.push(s.behind > 0 ? t.behind(s.behind) : s.ahead > 0 ? t.ahead(s.ahead) : t.onTrack)
  lines.push(`${t.end}: ${t.plan} ${s.plannedEnd ?? '—'} · ${t.atPace} ${s.projectedEnd ?? '—'}`)
  lines.push(`${t.concepts}: ${s.pendingConcepts} · ${t.buffer} ${s.bufferLeft}/${s.bufferTotal}`)
  if (s.daysIdle !== null && s.daysIdle >= IDLE_DAYS) lines.push(t.idle(s.daysIdle))
  return lines.join('\n')
}

async function activate($: EngineInterface): Promise<StudySummary | null> {
  await update($, isActive, () => true)

  return refresh($)
}

// Only a study session reads the plan and shows the status line.
async function refresh($: EngineInterface): Promise<StudySummary | null> {
  if (!(await read($, isActive))) {
    $.ui.status(undefined)
    return null
  }
  const loaded = await load($).catch((error: unknown) => `study-companion: ${String(error)}`)
  if (typeof loaded === 'string') {
    await update($, problem, () => loaded)
    $.ui.status(undefined)
    return null
  }
  await update($, summary, () => loaded)
  await update($, problem, () => null)
  $.ui.status(statusLine(loaded))
  return loaded
}

// The action that moves the current session forward, by its state.
function nextStep(s: StudySummary, t: Words): { label: string; command: string } | null {
  if (!s.next) return null
  if (s.next.status === 'studied') return { label: t.evaluate, command: 'study-eval' }
  if (s.next.status === 'evaluated') return { label: t.close, command: 'study-close' }
  return { label: t.open(pad(s.next.session)), command: 'study-next' }
}

// Runs a slash command as if typed; the toast confirms the click or says why it failed.
async function runCommand($: EngineInterface, t: Words, command: string): Promise<void> {
  $.ui.toast(t.running(command))
  await $.command.run({ command }).catch((error: unknown) => $.ui.toast(`/${command}: ${String(error)}`, { timeoutMs: 8000 }))
}

// Box-drawing lines render in every surface's font, unlike shade blocks.
const bar = (done: number, total: number, width: number) => {
  const filled = total > 0 ? Math.round((done / total) * width) : 0
  return { filled: '━'.repeat(filled), empty: '─'.repeat(width - filled) }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'study-today',
      description: 'Where your active study plan stands, without calling the model; opens the study pane',
    })
    const plan = await resolvePlan($).catch(() => null)
    const isInPlan = plan !== null && (e.cwd === plan.path || e.cwd.startsWith(`${plan.path}/`))
    const loaded = isInPlan ? await activate($) : await refresh($)
    if (loaded && loaded.daysIdle !== null && loaded.daysIdle >= IDLE_DAYS) {
      $.ui.toast(words(loaded.language).nudge(loaded.daysIdle, loaded.slug), { timeoutMs: 8000 })
    }
    $.clock.every(REFRESH_MS, () => void refresh($))

    return next(e)
  })

  on('command.run', { command: 'study-today' }, async $ => {
    const loaded = await activate($)
    await $.ui.open({ id: PANE, title: loaded ? words(loaded.language).title : 'Study' })
    if (!loaded) return { text: (await read($, problem)) ?? 'No active study plan.' }

    return { text: summaryText(loaded) }
  })

  on('skill.prompt', async ($, e, next) => {
    const prompt = await next(e)
    if (e.skill.startsWith('study-')) await activate($)

    return prompt
  })

  // A study command may have changed the plan: re-read it once the turn ends.
  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    await refresh($)

    return done
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const s = await read($, summary)
    const issue = await read($, problem)

    if (!s) {
      return (
        <Box flexDirection="column" gap={1}>
          <Text dimColor>{issue ?? WORDS.en.loading}</Text>
          <Button key="refresh" label={WORDS.en.refresh} onPress={() => void refresh($)} />
        </Box>
      )
    }

    const t = words(s.language)
    const step = nextStep(s, t)
    const width = Math.max(8, Math.min(24, e.props.bodyColumns - 12))
    const progress = bar(s.closed, s.total, width)
    const drift = s.behind > 0 ? t.behind(s.behind) : s.ahead > 0 ? t.ahead(s.ahead) : t.onTrack
    const isIdle = s.daysIdle !== null && s.daysIdle >= IDLE_DAYS

    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="column">
          <Text bold>{s.topic}</Text>
          <Text>
            <Text color="green">{progress.filled}</Text>
            <Text dimColor>{progress.empty}</Text> {s.closed}/{s.total}
          </Text>
        </Box>
        <Box flexDirection="column">
          {s.next ? (
            <Text>
              {t.next}: <Text bold>{pad(s.next.session)}</Text> {s.next.title}
            </Text>
          ) : (
            <Text>{t.noNext}</Text>
          )}
          {s.next && (
            <Text dimColor>
              {t.status[s.next.status] ?? s.next.status}
              {s.next.plannedDate ? ` · ${t.planned} ${s.next.plannedDate}` : ''}
            </Text>
          )}
        </Box>
        <Box flexDirection="column">
          <Text color={s.behind > 0 ? 'yellow' : 'green'}>{drift}</Text>
          {isIdle && <Text color="yellow">{t.idle(s.daysIdle ?? 0)}</Text>}
          <Text dimColor>
            {t.end}: {t.plan} {s.plannedEnd ?? '—'} · {t.atPace} {s.projectedEnd ?? '—'}
          </Text>
          <Text dimColor>
            {t.buffer} {s.bufferLeft}/{s.bufferTotal} · {t.concepts}: {s.pendingConcepts}
          </Text>
          <Text dimColor>
            {t.lastEval}:{' '}
            {s.lastEval
              ? `${pad(s.lastEval.session)} · ${s.lastEval.score} · ${s.lastEval.passed ? t.passed : t.failed} (${s.lastEval.date})`
              : t.none}
          </Text>
        </Box>
        <Box flexDirection="row" flexWrap="wrap" gap={1}>
          {step && (
            <Button
              key="step"
              label={step.label}
             
              variant="primary"
              onPress={() => runCommand($, t, step.command)}
            />
          )}
          <Button key="details" label={t.details} onPress={() => runCommand($, t, 'study-status')} />
          <Button key="refresh" label={t.refresh} onPress={() => void refresh($)} />
          <Button key="hide" label={t.hide} role="dismiss" onPress={() => void $.ui.close({ id: PANE })} />
        </Box>
      </Box>
    )
  })
}
