import { describe, expect, test } from 'claude-code/testing'

import { countPending, statusLine, toSummary } from './register'

const STATUS = {
  total: 28,
  closed: 4,
  next: { session: 5, title: 'Auditoría: CloudTrail', status: 'pending', planned_date: '2026-09-28' },
  behind_sessions: 7,
  ahead_sessions: 0,
  buffer_total: 3,
  buffer_left: 3,
  planned_end: '2026-10-29',
  projected_end: '2027-03-24',
  last_eval: { session: 4, score: '8/8', passed: true, date: '2026-09-25' },
  days_since_last_activity: 12,
  plan: { slug: 'aws-clf-c02', topic: 'AWS CLF-C02', language: 'es' },
}

const PLAN = [
  '<!-- study:concepts:begin -->',
  '| # | Concepto | Error | Se enseña en | Estado | Último cambio |',
  '|---|---|---|---|---|---|',
  '| 1 | A | x | 2 | confirmed | 2026-09-24 |',
  '| 2 | B | x | 3 | pending | 2026-09-11 |',
  '| 3 | C | x | 1 | consolidated | 2026-09-23 |',
  '| 4 | D | x | 1 | explained | 2026-09-23 |',
  '<!-- study:concepts:end -->',
].join('\n')

describe('summary helpers', () => {
  test('counts every concept that is not consolidated', () => {
    expect(countPending(PLAN)).toBe(3)
    expect(countPending('no concepts region')).toBe(0)
  })

  test('status line names plan, next session, progress and drift', () => {
    expect(statusLine(toSummary(STATUS, 3))).toBe('📚 aws-clf-c02 · S05 · 4/28 · 7 atrás')
    const onTrack = toSummary({ ...STATUS, behind_sessions: 0, plan: { ...STATUS.plan, language: 'en' } }, 0)
    expect(statusLine(onTrack)).toBe('📚 aws-clf-c02 · S05 · 4/28')
  })
})

test('/study-today answers from the script without the model and fills the pane', async ($, on) => {
  on('env.get', () => ({ value: '/home/test' }))
  on('process.run', ($, e) => ({
    value: {
      exitCode: 0,
      stdout: e.argv.includes('resolve') ? '/plans/aws\n' : JSON.stringify(STATUS),
      stderr: '',
      isStdoutTruncated: false,
      isStderrTruncated: false,
    },
  }))
  on('fs.read', () => ({ value: PLAN }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.open', () => ({ value: { isPlaced: true } }))

  const ran = await $.command.run({
    command: 'study-today',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: true, columns: 160 },
  })
  expect(ran.text).toContain('S05 · Auditoría: CloudTrail (pendiente)')
  expect(ran.text).toContain('7 sesiones de atraso')
  expect(ran.text).toContain('Conceptos por corregir: 3')

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'study-companion',
      surface,
      component: 'Pane',
      requestId: 'study',
      props: { title: 'Estudio', isFocused: false, bodyColumns: 40, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
    })
    expect(await ui.find({ type: 'Button', key: 'step', text: 'Abrir S05' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /12 días sin estudiar/ })).toBeDefined()
    await ui.unmount()
  }
})

test('the status line shows only once the session studies', async ($, on) => {
  const shown: (string | undefined)[] = []
  on('env.get', () => ({ value: '/home/test' }))
  on('process.run', ($, e) => ({
    value: {
      exitCode: 0,
      stdout: e.argv.includes('resolve') ? '/plans/aws\n' : JSON.stringify(STATUS),
      stderr: '',
      isStdoutTruncated: false,
      isStderrTruncated: false,
    },
  }))
  on('fs.read', () => ({ value: PLAN }))
  on('ui.status', ($, e) => {
    shown.push(e.text)
    return { value: undefined }
  })
  on('ui.toast', () => ({ value: undefined }))
  on('command.register', ($, e) => ({ value: { command: e.name } }))
  on('clock.every', () => ({ value: undefined }))
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('skill.prompt', ($, e) => ({ text: e.text }))

  await $.session.start({ cwd: '/work/other-repo', surface: 'terminal', isInteractive: true })
  expect(shown.filter(text => text !== undefined)).toEqual([])

  await $.skill.prompt({ skill: 'study-next', text: 'open the next session' })
  expect(shown.at(-1)).toBe('📚 aws-clf-c02 · S05 · 4/28 · 7 atrás')
})
