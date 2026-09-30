---
# Plan configuration, machine-read by study_state.py. Edit values, keep keys.
slug: {{slug}}
topic: {{topic}}
language: {{language}}              # es | en | pt (see language.md): content language of this plan
goal_type: {{goal_type}}            # exam | tool | course | other
horizon: {{horizon}}                # fixed | flexible | open
target_date: {{target_date}}        # YYYY-MM-DD when horizon=fixed, else null
target_week: {{target_week}}        # Monday of the target week when flexible, else null
start_date: {{start_date}}
cadence: {{cadence}}                # daily | weekdays | days:mon,wed,fri | per_week:N
session_minutes: {{session_minutes}}
external_followup: {{external_followup}}   # true if someone else tracks progress
milestones: {{milestones}}          # external dates, comma-separated YYYY-MM-DD, or null
video_platforms: {{video_platforms}}  # platzi,manual | platzi | manual | none
videos_status: {{videos_status}}    # ok | unavailable | none
# Evaluation protocol parameters: study-eval reads these. Edit to tune.
threshold_session: 80
threshold_checkpoint: 80
threshold_mock_first: 70
threshold_mock_final: 85
threshold_integrative: 80
eval_session_min: 5
eval_session_max: 15
minutes_per_question: 7
created: {{created}}
---

# {{plan_title}}

> {{txt_living_doc}}

## {{h_state}}

<!-- study:state:begin -->
<!-- study:state:end -->

## {{h_how_to_use}}

{{txt_how_to_use}}

## {{h_calendar}}

{{txt_calendar_note}}

{{milestones_line}}

<!-- study:calendar:begin -->
<!-- study:calendar:end -->

## {{h_syllabus}}

{{syllabus}}

## {{h_baseline}}

{{baseline}}

## {{h_concepts}}

{{txt_concepts_note}}

<!-- study:concepts:begin -->
{{tbl_concepts}}
|---|---|---|---|---|---|
<!-- study:concepts:end -->

## {{h_params}}

{{txt_params_note}}

## {{h_log}}

<!-- study:log:begin -->
{{tbl_log}}
|---|---|---|---|---|---|---|
<!-- study:log:end -->

## {{h_closures}}

_{{txt_closures_note}}_

## {{h_sources}}

{{tbl_sources}}
|---|---|---|
{{sources}}

{{txt_sources_note}}

## {{h_appendix}}

{{txt_appendix_note}}

{{checklist}}
