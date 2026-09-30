# Language — which language goes where

Two languages can differ, and each has one job:

- **Plan language** (`language:` in PLAN.md): what the files are written in.
- **Conversation language**: what you say to the user, turn by turn.

A typical case: someone studies for an exam taken in English while chatting in Spanish. The
plan is `en`; the conversation stays in Spanish.

## Plan language — inferred, confirmed, rarely asked

`study-new` does not ask a language question. It decides in this order:

1. **Explicit request wins**: "the files in English", "en español", "quero em português".
2. **Otherwise, the language of the request** that started the plan: `/study-new i want to
   learn laravel 12` → `en`; "quiero estudiar AWS" → `es`.
3. **Ask only when it is genuinely unclear**: the request has no text (`/study-new` alone), it
   mixes languages, or the only text is a proper name ("Laravel 12").

Confirm it in the summary screen as one line (*"Files in: English"*), where the user approves
everything anyway and can change it.

**Supported languages** are the columns of `labels.md` (today `es`, `en`, `pt`). For any other,
offer two options: English labels, or translating the fixed texts of `labels.md` into that
language once, at generation time, and using that translation for every file of the plan.
Record the choice in PLAN.md's `language:` comment.

Readings follow the plan language when an official localized version exists
(`interview.md`, *Documentation in the plan's language*).

## Conversation language — follows the user

- Reply in the language of the user's **latest message**.
- A bare command with no text (`/study-next`) → the last language the user wrote in this
  conversation; with none yet, the plan language.
- An explicit request ("speak to me in English") holds until the user changes it.

## What stays in the plan language even when chatting in another

| Content | Language |
|---|---|
| Everything written to files: sessions, PLAN.md regions, results, concepts, weak items | plan language |
| Evaluation questions and options | plan language: they come from the readings and get recorded. "Ask me in Spanish" switches that one evaluation only |
| Corrections of errors | conversation language, quoting terms from the source as they appear |
| `study-close` notes | **the user's own words, untranslated**: their wording is the point. Headings and fixed text stay in the plan language |

## Spanish is neutral Spanish

For Spanish, in files and in conversation: address the user as *tú*, never voseo (*tenés,
podés, marcá, quedate*), no regionalisms (*de a uno, acá, chequear, rendir un examen*). This holds
even when the user writes with voseo or a regional variety, because plans get shared. Use a
regional variety only if the user explicitly asks for it, and record that in the `language:`
comment. The user's own notes are not rewritten: see the table above.
