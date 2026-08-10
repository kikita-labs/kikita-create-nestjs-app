# Versioning

`plugin.json`'s `version` field is the only version signal the Agent Plugins spec defines.
There's no required changelog file, but tagging the release commit on `main` is good
practice for anyone pinning a specific version of this plugin.

## SemVer meaning for this plugin

- **Patch** (`1.0.x`) — wording/typo fixes in `SKILL.md`/`plan.md`/templates, no behavior
  change, no file added or removed.
- **Minor** (`1.x.0`) — new questionnaire question, new gated template file, new generated
  doc — backward compatible: existing scaffolded projects still update cleanly via
  `update.md`.
- **Major** (`x.0.0`) — breaking change: an existing questionnaire answer's meaning changed,
  a generated project's structure changed in a way `update.md` can no longer cleanly
  diff/merge, or a previously required file/step was removed.

## How to bump

- Bump `version` in the same commit as the change that justifies it — never a separate
  "bump version" commit.
- Tag the merge commit on `main` if this is a point worth pinning:
  `git tag v<version> && git push origin v<version>` — tags don't travel with a normal
  branch push, push them explicitly.

## Not to be confused with `.kikita-scaffold.json`

A scaffolded project's `.agents/.kikita-scaffold.json` records `scaffoldedFromCommit` — an
exact git commit hash, not this plugin's `version`. That's what `update.md` actually diffs
against; it's per-project and precise. `plugin.json`'s `version` is a coarser, human-facing
signal for this repo as a whole and plays no role in the diff/merge logic.

## Review Checklist

- [ ] `version` bumped if the change is more than a wording fix.
- [ ] Bump is in the same commit as the change, not a follow-up.
- [ ] Tagged on `main` if this is a release point worth pinning.
