export type StudyNext = {
  session: number
  title: string
  status: string
  plannedDate: string | null
}

export type StudyEval = { session: number; score: string; passed: boolean; date: string }

export type StudySummary = {
  slug: string
  topic: string
  language: string
  closed: number
  total: number
  next: StudyNext | null
  behind: number
  ahead: number
  bufferLeft: number
  bufferTotal: number
  plannedEnd: string | null
  projectedEnd: string | null
  lastEval: StudyEval | null
  daysIdle: number | null
  pendingConcepts: number
}

declare module 'claude-code' {
  interface PluginState {
    'study-companion': { summary: StudySummary | null; problem: string | null }
  }
}
