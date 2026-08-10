# Documentation & File Relationships

This repo has two documentation layers. Keep them separate — editing the wrong one is the
most common mistake here.

1. **This repo's own docs** — `AGENTS.md`, `.agents/`, root `README.md`. Describe how to
   develop and maintain *this plugin*.
2. **The template payload** — `skills/kikita-create-nestjs-app/templates/`. Describes and
   generates docs for *the NestJS project this skill scaffolds*. Its `AGENTS.md`,
   `CLAUDE.md`, and `.agents/*.md` are template source: copied, with placeholders resolved,
   into a user's generated project. Editing them changes future scaffolded projects — it has
   no effect on this repo.

## Skill logic files

All under `skills/kikita-create-nestjs-app/`:

- `SKILL.md` — entry point: mode detection (init/adopt/update), the two-stage
  questionnaire, generation rules. Read first when changing skill behavior.
- `plan.md` — step-by-step fresh-init sequence.
- `adopt.md` — retrofit sequence for an existing (non-scaffolded) NestJS project.
- `update.md` — diff/merge sequence for an already-scaffolded project. Contains `git -C
  <plugin-root>` commands hardcoded to the `skills/kikita-create-nestjs-app/templates/`
  path — keep those in sync if this repo's layout ever changes again.
- `checklist.md` — post-init verification the skill runs before reporting success.

## Template conventions (inside `templates/`)

- `{{PLACEHOLDER}}` tokens are resolved from questionnaire answers at generation time.
  They're *supposed* to be there in this repo's copy — that's what makes it a template. Never
  "fix" one by hardcoding a value; that breaks generation for every other answer combination.
- `<!-- SCAFFOLD: ... -->` comments mark inclusion gates — a whole file or block copied only
  if the matching questionnaire answer says so (e.g. `core/auth.md`, `core/queue.md`,
  `core/cache.md`, `core/storage.md`, `core/messaging.md`, `core/i18n.md`, and the
  bot-transport docs are all gated on their matching feature/platform answer). When editing
  near a gate comment, keep it attached to the right block; losing it silently makes the gate
  stop working.
- A new file under `templates/.agents/` must be linked from
  `templates/.agents/README.md` (and from `templates/AGENTS.md` if it's a "must read"), or
  generated projects ship an orphaned doc.

## When to update what

- Changed a questionnaire question or generation rule? → `SKILL.md` + `plan.md` (+
  `update.md` if it affects the diff/merge logic).
- Changed template content or a convention it documents? → the file(s) under `templates/`,
  plus `templates/.agents/README.md` if a file was added or removed.
- Changed install steps, repo structure, or what the skill does at a glance? → root
  `README.md`.
- Changed `plugin.json` metadata or the package layout? → see `versioning.md`.

## Review Checklist

- [ ] Change made in the correct layer — this repo's own docs vs. the template payload.
- [ ] No unresolved `{{PLACEHOLDER}}` left in a file that isn't supposed to have one (i.e.
      outside `templates/`).
- [ ] `templates/.agents/README.md` updated if a template doc was added or removed.
- [ ] Root `README.md` updated if install/structure/behavior changed.
