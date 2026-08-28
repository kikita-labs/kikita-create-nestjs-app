# kikita-create-nestjs-app

An agent skill that scaffolds a brand-new NestJS project (latest stable) — REST API, a bot on
any platform (Telegram, Discord, or another), or both in the same app — and generates a full
`.agents/` documentation tree alongside it, so any AI agent working in the project afterwards has
a complete, self-maintaining source of truth from commit one.

Packaged as an [Agent Skill](https://agentskills.io) — an open, portable format usable by
any compatible client (Claude Code, Codex, Cursor, GitHub Copilot, VS Code, Kiro, …), not
just one product.

See [`skills/kikita-create-nestjs-app/SKILL.md`](./skills/kikita-create-nestjs-app/SKILL.md) for
what it does, [`plan.md`](./skills/kikita-create-nestjs-app/plan.md) for the exact step-by-step
scaffolding sequence, and [`checklist.md`](./skills/kikita-create-nestjs-app/checklist.md) for
the post-init verification it runs before handing the project back to you.

## What it generates

- `CLAUDE.md` → `AGENTS.md` → `.agents/*.md` — the full documentation tree, described in
  [`templates/.agents/README.md`](./skills/kikita-create-nestjs-app/templates/.agents/README.md).
- A working NestJS app: latest stable Nest CLI, Prisma + Postgres, global `ValidationPipe`
  (`class-validator`/`class-transformer`), Zod-validated env config, `nestjs-pino` structured
  logging, ESLint (`@darraghor/eslint-plugin-nestjs-typed`) + Prettier + Husky pre-wired, a local
  `docker-compose.yml` (Postgres always, Redis/RabbitMQ if the matching feature was chosen).
- A feature-based `src/` layout: small features stay together, large features split into named
  capability folders, and `src/core/` remains reserved for app-wide singleton infrastructure.
- A mandatory per-file review gate after every source change: it checks ownership and placement,
  reusable declarations/entities/constants, decomposition thresholds, test coverage, comments, and
  module wiring. ESLint also blocks hand-written files over 400 lines and functions over 120 lines.
- REST branch: Swagger at `/docs`, URI versioning (`/v1/...`), env-driven CORS allowlist.
- Bot branch: generic Update-handler transport pattern, with concrete adapters for
  `nestjs-telegraf` (Telegram) and `necord` (Discord) — see
  [`templates/.agents/architecture/transport-adapter.md`](./skills/kikita-create-nestjs-app/templates/.agents/architecture/transport-adapter.md).
- A two-stage pre-init questionnaire (application type/platform first, then tests, auth, queue,
  cache, file uploads, messaging, TSDoc policy, git policy, package manager, git remote) drives
  which docs and config get generated — see `SKILL.md` for why it's staged, not one flat list.

## Install

This repo follows the [Agent Skills spec](https://agentskills.io/specification): the actual
skill is the `skills/kikita-create-nestjs-app/` directory, with `SKILL.md` at its root. The
spec doesn't define an update mechanism, so this skill's own `update.md` falls back to git:
it walks up from wherever `SKILL.md` is running to find a `.git`, then diffs against
upstream. That means the installed skill folder must still be inside a real git clone — a
bare `cp` that drops `.git` breaks updates silently (see the Update section below).

Since clients expect `SKILL.md` directly at the top of the installed skill folder, but the
clone's `SKILL.md` sits one level down (`skills/kikita-create-nestjs-app/`), install by
cloning the repo to a fixed source location once, then linking the client's skills folder to
the subdirectory inside it — a symlink (or, on Windows, a directory junction, which unlike a
symlink needs no admin rights) keeps `.git` reachable through the link.

### Claude Code

**Personal (all your projects), macOS/Linux:**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git ~/.kikita-create-nestjs-app-src
ln -s ~/.kikita-create-nestjs-app-src/skills/kikita-create-nestjs-app ~/.claude/skills/kikita-create-nestjs-app
```

**Personal, Windows (PowerShell):**

```powershell
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git "$HOME\.kikita-create-nestjs-app-src"
New-Item -ItemType Junction -Path "$HOME\.claude\skills\kikita-create-nestjs-app" -Target "$HOME\.kikita-create-nestjs-app-src\skills\kikita-create-nestjs-app"
```

**Project-scoped (this project only, committed to the repo), macOS/Linux:**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git .kikita-create-nestjs-app-src
ln -s ../../.kikita-create-nestjs-app-src/skills/kikita-create-nestjs-app .claude/skills/kikita-create-nestjs-app
```

Add `.kikita-create-nestjs-app-src/` to the project's `.gitignore` (it's a vendored clone,
not this project's own source) — commit only the symlink/junction under `.claude/skills/`.

Claude Code picks up new/changed skills under `~/.claude/skills/` and `.claude/skills/` live,
within the current session — no restart needed, unless the top-level `.claude/skills/` directory
didn't exist yet when the session started (in that case restart once).

### Codex

Codex does **not** use `$CODEX_HOME` or `.codex/skills` for skills — that's a common but
incorrect claim floating around. The real locations, per Codex's own docs, same
clone-then-link pattern as above:

**User scope (all your projects), macOS/Linux:**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git ~/.kikita-create-nestjs-app-src
ln -s ~/.kikita-create-nestjs-app-src/skills/kikita-create-nestjs-app "$HOME/.agents/skills/kikita-create-nestjs-app"
```

**Repo scope (this project, and any subdirectory under it), macOS/Linux:**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git .kikita-create-nestjs-app-src
ln -s ../.kikita-create-nestjs-app-src/skills/kikita-create-nestjs-app .agents/skills/kikita-create-nestjs-app
```

On Windows use `New-Item -ItemType Junction` as shown for Claude Code above, pointed at
`.agents/skills/kikita-create-nestjs-app` instead.

Codex scans `.agents/skills` in the current directory and every parent up to the repo root. If a
newly installed or updated skill doesn't show up, restart Codex.

### Other Agent-Skills-compatible clients

Any client that implements the [Agent Skills spec](https://agentskills.io/specification) can
load the skill straight from `skills/kikita-create-nestjs-app/` in a clone of this repo —
refer to that client's own docs for its install command, since the spec defines the skill
folder format, not a universal installer.

## Use

From an empty (or near-empty) directory where you want a new NestJS app:

```
/kikita-create-nestjs-app
```

The agent asks the staged questionnaire, then follows `plan.md` end to end: scaffold the app,
wire Prisma/validation/logging/transport, set up tooling, generate the `.agents/` doc tree, set
up git, and run `checklist.md` before telling you it's done.

## Update

Already scaffolded a project with this skill and the templates have moved on since? Run the
exact same command inside that project:

```
/kikita-create-nestjs-app
```

The skill detects `.agents/.kikita-scaffold.json` (written at scaffold time) and switches to
update mode instead of re-running the questionnaire: it `git pull`s its own source clone,
diffs `skills/kikita-create-nestjs-app/templates/.agents/` between the commit the project was
scaffolded/last-updated from and the current `HEAD`, and merges what changed into the project's
`.agents/` files — never a blind overwrite, since those files usually pick up project-specific
edits after scaffolding. See [`update.md`](./skills/kikita-create-nestjs-app/update.md) for the
exact algorithm. This is why the Install section above always clones (never `cp`s) — without a
`.git` reachable from the installed skill folder, `update.md` has nothing to diff against and
update mode can't run.

This works the same way whether you're driving the agent by hand or a fully agent-driven
("vibecoding") workflow that never opens the project directly — it's the same slash command
either way, no separate `-update` skill to install or remember.

## Scope

Single deployable app, not a monorepo/Nx workspace and not a distributed microservices topology
(multiple services/repos). A message broker, if chosen, wires a hybrid setup
(`app.connectMicroservice()`) inside the same single app — it never spins up a second service.
See [`templates/.agents/architecture/messaging.md`](./skills/kikita-create-nestjs-app/templates/.agents/architecture/messaging.md).

## License

[MIT](./LICENSE)
