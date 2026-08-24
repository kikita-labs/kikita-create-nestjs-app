# Versioning

The [Agent Skills spec](https://agentskills.io/specification) doesn't define a version
field or an update mechanism — it's just a folder format. `SKILL.md`'s optional `metadata`
map is the only spec-sanctioned place to record a human-facing version string, and clients
don't read it automatically. So the real source of truth for this repo's version is git
itself: every release **must** get a matching git tag and GitHub release — not "when it
seems worth it." A `metadata.version` bump with no tag is an incomplete change, full stop; a
bump that ships without one is a bug in the PR that introduced it, not a follow-up someone
can do "later."

## SemVer meaning for this skill

- **Patch** (`1.0.x`) — wording/typo fixes in `SKILL.md`/`plan.md`/templates, no behavior
  change, no file added or removed.
- **Minor** (`1.x.0`) — new questionnaire question, new gated template file, new generated
  doc — backward compatible: existing scaffolded projects still update cleanly via
  `update.md`.
- **Major** (`x.0.0`) — breaking change: an existing questionnaire answer's meaning changed,
  a generated project's structure changed in a way `update.md` can no longer cleanly
  diff/merge, or a previously required file/step was removed.

## How to bump

1. Bump `metadata.version` in `skills/kikita-create-nestjs-app/SKILL.md`'s frontmatter, in
   the same commit as the change that justifies it — never a separate "bump version" commit.
2. Get the PR merged into `main` (branch protection requires this anyway).
3. Immediately after merging — same sitting, not a later session — tag and release the
   merge commit on `main`:
   ```sh
   git checkout main && git pull --ff-only
   git tag v<version>
   git push origin v<version>
   gh release create v<version> --title "v<version>" --notes "<what changed and why>"
   ```
4. Confirm the tag and release actually show up on GitHub (`gh release view v<version>`)
   before considering the version bump done. Pushing the tag and creating the release are
   two separate commands — doing one without the other is still an incomplete bump.

There is no such thing as a version bump that's "too small to tag." Patch, minor, or major —
every one gets a tag and a release. If a change doesn't feel worth tagging, that's a sign
it wasn't actually worth a version bump either — reconsider the bump, not the tag.

## What actually drives updates: git, not the version string

`metadata.version` is a coarse, human-facing label — nothing in this repo's own tooling
reads it. `update.md`'s diff/merge logic runs entirely off git: an installed skill is a
symlink/junction into a real clone of this repo (see `README.md`'s Install section), and
`update.md` resolves that clone's `.git`, `git pull`s it, and diffs commits — never the
version string. Tagging still matters because it gives humans (and release notes) a
meaningful anchor, but a missing tag doesn't break `update.md`; a missing `.git` does.

## Not to be confused with `.kikita-scaffold.json`

A scaffolded project's `.agents/.kikita-scaffold.json` records `scaffoldedFromCommit` — an
exact git commit hash, not this skill's `metadata.version`. That's what `update.md` actually
diffs against; it's per-project and precise.

## Review Checklist

- [ ] `metadata.version` in `SKILL.md` bumped if the change is more than a wording fix.
- [ ] Bump is in the same commit as the change, not a follow-up.
- [ ] Tag `v<version>` pushed to `origin` after the PR merged.
- [ ] GitHub release created for that tag (`gh release view v<version>` succeeds).
- [ ] Not left "for later" — done in the same sitting as the merge.
