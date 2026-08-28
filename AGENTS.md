# AGENTS.md

Instructions for anyone — human or AI agent — working **on this repo**: the
`kikita-create-nestjs-app` Agent Skill itself. This is not the same thing as
[`skills/kikita-create-nestjs-app/templates/AGENTS.md`](./skills/kikita-create-nestjs-app/templates/AGENTS.md),
which is a *template file* this skill copies into projects it scaffolds — editing that one
changes what future generated projects look like, not this repo's own rules.

## Must read

- [.agents/workflow.md](./.agents/workflow.md) — task sequence for any change here.
- [.agents/git-policy.md](./.agents/git-policy.md) — commit/branch/PR rules.
- [.agents/documentation.md](./.agents/documentation.md) — how `SKILL.md`/`plan.md`/
  `templates/` relate, and the placeholder/gate conventions inside `templates/`.

## Read when relevant

- [skills/kikita-create-nestjs-app/upgrade.md](./skills/kikita-create-nestjs-app/upgrade.md) — when
  upgrading a legacy or copied skill installation before updating a project's docs.
- [.agents/versioning.md](./.agents/versioning.md) — when and how to bump `SKILL.md`'s
  `metadata.version` and tag a release.
- [.agents/testing-and-quality.md](./.agents/testing-and-quality.md) — the CI checks and how
  to run them locally before pushing.

## Non-negotiable rules

- Never add `Co-authored-by`, `Claude-Session`, or any other AI-attribution line to a commit
  message — in this repo or any other. No exceptions, ever.
- All work happens on a feature branch, merged via PR — `main` is branch-protected and
  rejects direct pushes, including from the repo owner.
- English only in every tracked file — no Cyrillic, no mojibake. Enforced by CI.
- Don't confuse this repo's own docs with the `templates/` payload:
  `skills/kikita-create-nestjs-app/templates/AGENTS.md`, `.../CLAUDE.md`, and
  `.../templates/.agents/*` describe the *generated NestJS project*, not this repo.
