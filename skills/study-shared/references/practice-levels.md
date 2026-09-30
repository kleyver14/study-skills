# Practice — three levels, chosen per area by access, not by topic

Practice is optional per session. The session is complete without it, and it never counts
toward the evaluation threshold. It speeds learning up when it is possible; it never gates it.

| Level | When | Generate |
|---|---|---|
| `live` | the user has real access to that area | exercises against their own environment, each preceded by a one-line comment saying **what the output will show and why it matters** |
| `sandbox` | no access, but a free or local alternative exists **and you verified it exists** | free tier, official playground, local emulator, online console, with the verified link |
| `none` | nothing to touch, or the topic is conceptual | *explain it back in your own words* prompts (they feed the `study-close` notes) and worked examples using real output taken from the official source |

## What `live` may do

Where the practice runs decides this, not the topic:

- **Shared or production environments** (the company's cloud account, a team repo, a shared
  database): **read-only commands only**. Nothing that creates, modifies or deletes.
- **The learner's own disposable environment** (a local project for a framework, a personal
  sandbox account, a container they just started): modifying it *is* the practice, so create,
  migrate, run and delete freely. Say it is theirs to break, and end cloud exercises with a
  cleanup step when resources cost money.

When unsure which one it is, treat it as shared.

## Commands must run as-is

- The user's identity decides what a command can refer to. Ask how they authenticate in the
  interview (for AWS: IAM user, or IAM Identity Center / SSO role), and resolve it before writing
  commands (`aws sts get-caller-identity` or the tool's equivalent). Someone who signs in through
  a role has no "own IAM user": commands about "your user" do not apply to them.
- **No placeholders inside executable code blocks.** `<your-user>` makes zsh fail with a parse
  error, and the desktop app's Run button runs the block literally. Put the real value in; if it
  truly cannot be known, show it as inline code in CAPITALS (`BUCKET_NAME`) outside the block and
  say what to replace.
- One command per code block when the user may press Run on it.
- If a command **costs money** (metered APIs, such as cloud cost-explorer endpoints billed per
  request), warn before suggesting it and prefer a free alternative.

## When a command fails

A `live` command that fails for permissions is **data, not an error**: note it in the session's
`weak` or `notes` region, downgrade that area to `sandbox` or `none` in the remaining sessions'
frontmatter, and stop proposing that access.

Never assume the user's environment looks like the AWS example this family was born from. The
interview's access question decides; the topic does not.
