# Drift, recovery and replan — study-next and study-status

Drift is measured in `study-next` every time: `behind_sessions` = non-closed sessions whose
`planned_date` is already past. The policy depends on the plan's `horizon`.

## flexible or open

Re-project from today and say it in one line, quoting the **planned end** from `status`:
*"You are 2 sessions behind; the plan now ends on Dec 20 instead of Dec 6."*
Mention `target_week` only if the new planned end crosses it; otherwise the two dates are
unrelated and quoting it would be false.
`study_state.py project <plan> --start <today-or-next-cadence-day> --from-session <next>`
(today counts if it is a cadence day).

## fixed

Propose, in this order, showing the resulting calendar each time, and apply only on approval:

1. **Consume buffer** — while `buffer_left > 0`: mark the next buffer session(s) as the
   absorbers by re-projecting content sessions onto their dates and deleting or `closed`-marking
   the buffer session(s) consumed.
2. **Double up** — two sessions on one date, only when both are light (estimate by total
   reading minutes ≤ ~60% of `session_minutes` each).
3. **Trim** — merge or thin the lightest sessions. Show exactly what is lost before touching
   anything: a trimmed item is gone from the plan, not postponed.

If none of that fits: say so plainly and offer more sessions per week or moving the date.
Never re-plan silently, and never trim without showing the cost.

## Ahead of schedule

`ahead_sessions > 0` → say it and offer to pull the next session forward, use the slack to
deepen a weak area, or finish earlier. Do nothing unless asked.

## Buffer sessions when on track

If the next session is a buffer and there is no drift, offer to skip it (mark `closed` with a
note) or use it as review. Buffer is not spent automatically — it is the reserve for bad weeks.

## Replan (study-status replan)

Life changed the cadence or the deadline. Ask only cadence and horizon again, then:
`project --cadence <new> --start <today> --from-session <next>`; update `horizon`,
`target_date`/`target_week` in PLAN.md frontmatter with `set`. If `fixed` and it no longer fits,
enter the fixed-policy above. **Do not regenerate content** — move dates, and trim only through
the policy with the user's approval.

## After any re-projection: check the milestones

External milestones (dates in `milestones:`) never move. Re-projecting can push a checkpoint past
the milestone it was meant to precede, so run `study_state.py check <plan>` every time. For each
`milestone_without_checkpoint`, tell the user what will actually have been covered by that date
and offer to pull the checkpoint forward (move it to the last cadence day before the milestone).
Apply only with approval.

