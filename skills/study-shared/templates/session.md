---
session: {{n}}
slug: {{slug}}
title: {{title}}
status: pending                # pending | studied | evaluated | closed
planned_date: {{planned_date}}
actual_date: null
block: {{block}}
is_buffer: {{is_buffer}}
is_checkpoint: {{is_checkpoint}}
eval_type: {{eval_type}}       # session | checkpoint | mock | integrative | none
eval_score: null
eval_passed: null
eval_attempts: 0
eval_date: null
closed_date: null
practice_level: {{practice_level}}   # live | sandbox | none
video_minutes: {{video_minutes}}     # sum of the Videos section; never part of the session time
---

# {{h_session}} {{nn}} · {{title}}

**{{h_block}} {{block}}** · {{h_reading}} ~{{reading_minutes}} min{{video_line}}

## {{h_topic}}

**{{title}}**

{{why_it_matters}}

## {{h_what_to_study}}

{{checklist}}

## {{h_how_to_think}} — {{analogy_title}}

{{analogy_body}}

## {{h_readings}}

| {{h_col_resource}} | {{h_col_link}} | {{h_col_time}} |
|---|---|---|
{{readings}}

## {{h_videos}}

<!-- study:videos:begin -->
{{videos}}
<!-- study:videos:end -->

## {{h_practice}} ({{practice_level}})

{{practice_body}}

_{{txt_practice_optional}}_

---

<!-- study:eval-block:begin -->
{{eval_block}}
<!-- study:eval-block:end -->

### {{h_result}}

<!-- study:result:begin -->
_{{txt_not_taken}}_
<!-- study:result:end -->

---

## {{h_notes}}

<!-- study:notes:begin -->
_{{txt_notes_hint}}_
<!-- study:notes:end -->

## {{h_weak}}

<!-- study:weak:begin -->
_{{txt_weak_hint}}_
<!-- study:weak:end -->
