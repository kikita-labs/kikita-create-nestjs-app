# Update Plan

Runs when `/kikita-create-nestjs-app` (or an equivalent "update the project docs" request) is
invoked inside a directory that was already scaffolded by this skill — detected by the presence
of `.agents/.kikita-scaffold.json`. If that file is missing, this is a fresh init: follow
`plan.md` instead, not this file.

Model: same idea as `create-react-app-updater` / `ember-cli-update` — record the commit this
project was scaffolded (or last updated) from, diff the skill's own template tree between that
commit and its current `HEAD`, and merge the result into the project's live `.agents/` files
instead of overwriting them. The project's docs diverge after scaffolding (real project-specific
edits, extra ADRs, feature-specific rules) — an update must respect that, never blind-`cp` a
template over a customized file.

## 1. Locate the skill's own source

The Agent Skills spec has no update mechanism of its own, so this falls back to git. The
skill is running from wherever it was installed (`~/.claude/skills/kikita-create-nestjs-app`,
`.claude/skills/kikita-create-nestjs-app`, `~/.agents/skills/...`, `.agents/skills/...`, or an
equivalent location for another Agent-Skills-compatible client — see `README.md`'s Install
section). Per that section, the installed skill folder is a symlink/junction into a full git
clone of this repo, so its `.git` is reachable by walking up from the currently executing
`SKILL.md`'s own (resolved) location: run `git -C <path-to-running-skill-dir> rev-parse
--show-toplevel` to get `<plugin-root>`; don't guess or re-derive it another way. This skill's
own template tree then lives at `<plugin-root>/skills/kikita-create-nestjs-app/templates/`.

- If `git rev-parse --show-toplevel` fails (not inside a git working tree at all) — stop and
  tell the user: this install was made by copying files instead of cloning (or the link to
  the clone is broken), so there's no history to diff against; ask them to reinstall per
  `README.md`'s Install section before retrying the update.
- `git -C <plugin-root> status --porcelain` — if it reports local changes, stop and tell the user:
  this install has been hand-edited and pulling would risk losing that; ask how they want to
  proceed rather than pulling over it.
- Otherwise `git -C <plugin-root> pull --ff-only` to bring the template source current before
  diffing anything.

## 2. Read the project's scaffold record

Read `.agents/.kikita-scaffold.json` in the target project:

```json
{
  "skill": "kikita-create-nestjs-app",
  "scaffoldedFromCommit": "<git hash>",
  "answers": {
    "appType": "REST",
    "botPlatform": null,
    "tests": "unit+e2e",
    "auth": true,
    "queue": false,
    "cache": false,
    "storage": true,
    "messaging": false,
    "i18n": false,
    "jsdoc": true,
    "packageManager": "pnpm"
  }
}
```

`answers` is the original questionnaire record (`SKILL.md` section 1) — reuse it to resolve
`{{PLACEHOLDER}}` tokens and inclusion gates in upstream changes without re-asking questions the
user already answered, unless a diff specifically depends on an answer this record doesn't have
(e.g. the skill grew a new question after this project was scaffolded) — then ask only that one.

## 3. Diff since last sync

```
git -C <plugin-root> log --oneline <scaffoldedFromCommit>..HEAD -- skills/kikita-create-nestjs-app/templates/.agents
```

Empty output → docs are already current. Report that and stop; don't rewrite the scaffold
record for a no-op.

Otherwise, for every file under `skills/kikita-create-nestjs-app/templates/.agents/` touched
in that range:

```
git -C <plugin-root> diff <scaffoldedFromCommit>..HEAD -- skills/kikita-create-nestjs-app/templates/.agents/<relpath>
```

Map `skills/kikita-create-nestjs-app/templates/.agents/<relpath>` to the project path
`.agents/<relpath>`.

## 4. Apply per file

- **File exists in the project**: read it, read the upstream diff, and edit in the *intent* of
  the diff — same rule change, expressed against whatever the project's file already says
  (which may use different wording, different examples, or extra project-specific rules the
  template never had). Never replace the whole file with the new template contents; that
  destroys project-specific edits. If the project's file has already diverged so far that the
  diff's target text can't be located, stop on that file and describe the conflict instead of
  guessing.
- **File is new upstream** (added to `skills/kikita-create-nestjs-app/templates/.agents/` after this project's scaffold commit)
  and is a gated file (`core/auth.md`, `core/queue.md`, `core/cache.md`, `core/storage.md`,
  `core/messaging.md`, `core/i18n.md`, `agent-surface.md`, bot-specific transport docs): only
  add it if the stored `answers` say the gate is open for this project. Resolve any
  `{{PLACEHOLDER}}` in it from `answers`.
- `core/health.md` and `core/logging.md` are always-generated docs, not questionnaire-gated. Add
  them to an older project when they are new upstream, then update the relevant README/AGENTS
  links. For an adopted project, describe the implementation that actually exists and record gaps;
  do not claim that a missing logger feature is already wired.
- **File was deleted upstream**: don't delete the project's copy automatically — flag it and
  ask, since a project may still depend on content that got removed from the template for
  reasons specific to newer scaffolds.
- Update `.agents/README.md` / `AGENTS.md` links if a file was added or removed.

Confirm the set of changes with the user before writing anything wide (more than a couple of
files) — a one-line rule tweak in a single file can be applied directly, a multi-file docs
restructure should be previewed first.

## 5. Record the new sync point

After applying (or explicitly skipping) every changed file, update
`.agents/.kikita-scaffold.json`'s `scaffoldedFromCommit` to the plugin repo's current `HEAD`
(`git -C <plugin-root> rev-parse HEAD`). Do this even if some files were skipped on conflict —
those are called out in the report, not silently dropped, but re-running the update shouldn't
re-show already-reviewed changes for files that *were* applied.

## 6. Report

List, per file: `applied` / `skipped (conflict)` / `skipped (gate closed)` / `already current`.
Don't declare the docs "up to date" if anything was skipped — say what's still pending and why.
