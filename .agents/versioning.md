# Versioning

`plugin.json`'s `version` field is the only version signal the Agent Plugins spec defines.
There's no required changelog file, but every bump **must** get a matching git tag and
GitHub release — not "when it seems worth it." A `version` bump with no tag is an
incomplete change, full stop; a bump that ships without one is a bug in the PR that
introduced it, not a follow-up someone can do "later."

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

1. Bump `version` in the same commit as the change that justifies it — never a separate
   "bump version" commit.
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

## Tracking the Agent Plugins spec version itself

There are three different "versions" in play here — don't conflate them:

1. **This plugin's own `version`** in `plugin.json` — covered above.
2. **The Agent Plugins spec version** — pinned via `$schema` in `plugin.json`
   (`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`) and in `mcp.json` if one
   exists. This repo currently targets spec `1.0.0`.
3. **`.kikita-scaffold.json`'s `scaffoldedFromCommit`** — see below.

The spec itself can release a new major version (`2.0.0`, ...) independently of anything we
do. Nothing in this repo watches for that automatically — check periodically:

- Spec source of truth: https://github.com/agentplugins/agent-plugins-spec (releases/tags).
- Overview and guides: https://agent-plugins.org.

When a new spec version appears:

- **Don't bump `$schema` reflexively.** Read that version's changes first — the schema is a
  closed object (unknown top-level fields are rejected by conformant clients), so a careless
  bump can make `plugin.json` invalid for clients still validating against `1.0.0`, or drop
  support for clients that haven't adopted the new spec version yet.
- Treat a `$schema` bump as its own deliberate change: read the migration notes, update
  `plugin.json` and `mcp.json` (if present) together — their spec versions must match — run
  `check_plugin_json.py` locally, and bump this plugin's own `version` as a **major** bump
  (it changes what clients can load this plugin at all).
- Do this as a dedicated PR, not bundled with an unrelated content change.

## Not to be confused with `.kikita-scaffold.json`

A scaffolded project's `.agents/.kikita-scaffold.json` records `scaffoldedFromCommit` — an
exact git commit hash, not this plugin's `version`. That's what `update.md` actually diffs
against; it's per-project and precise. `plugin.json`'s `version` is a coarser, human-facing
signal for this repo as a whole and plays no role in the diff/merge logic.

## Review Checklist

- [ ] `version` bumped if the change is more than a wording fix.
- [ ] Bump is in the same commit as the change, not a follow-up.
- [ ] Tag `v<version>` pushed to `origin` after the PR merged.
- [ ] GitHub release created for that tag (`gh release view v<version>` succeeds).
- [ ] Not left "for later" — done in the same sitting as the merge.
