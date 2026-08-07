# kikita-create-nestjs-app

An agent skill that scaffolds a brand-new NestJS project (latest stable) — REST API, a bot on
any platform (Telegram, Discord, or another), or both in the same app — and generates a full
`.agents/` documentation tree alongside it, so any AI agent working in the project afterwards has
a complete, self-maintaining source of truth from commit one.

See [`SKILL.md`](./SKILL.md) for what it does, [`plan.md`](./plan.md) for the exact step-by-step
scaffolding sequence, and [`checklist.md`](./checklist.md) for the post-init verification it runs
before handing the project back to you.

## What it generates

- `CLAUDE.md` → `AGENTS.md` → `.agents/*.md` — the full documentation tree, described in
  [`templates/.agents/README.md`](./templates/.agents/README.md).
- A working NestJS app: latest stable Nest CLI, Prisma + Postgres, global `ValidationPipe`
  (`class-validator`/`class-transformer`), Zod-validated env config, `nestjs-pino` structured
  logging, ESLint (`@darraghor/eslint-plugin-nestjs-typed`) + Prettier + Husky pre-wired, a local
  `docker-compose.yml` (Postgres always, Redis/RabbitMQ if the matching feature was chosen).
- REST branch: Swagger at `/docs`, URI versioning (`/v1/...`), env-driven CORS allowlist.
- Bot branch: generic Update-handler transport pattern, with concrete adapters for
  `nestjs-telegraf` (Telegram) and `necord` (Discord) — see
  [`templates/.agents/architecture/transport-adapter.md`](./templates/.agents/architecture/transport-adapter.md).
- A two-stage pre-init questionnaire (application type/platform first, then tests, auth, queue,
  cache, file uploads, messaging, TSDoc policy, git policy, package manager, git remote) drives
  which docs and config get generated — see `SKILL.md` for why it's staged, not one flat list.

## Install

This is a skill for AI coding agents (Claude Code, Codex). Installing it means placing this
repo's contents under a `<skill-name>/` folder inside the agent's skills directory, so the
folder name matches this repo's name.

### Claude Code

**Personal (all your projects):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git ~/.claude/skills/kikita-create-nestjs-app
```

**Project-scoped (this project only, committed to the repo):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git .claude/skills/kikita-create-nestjs-app
```

Claude Code picks up new/changed skills under `~/.claude/skills/` and `.claude/skills/` live,
within the current session — no restart needed, unless the top-level `.claude/skills/` directory
didn't exist yet when the session started (in that case restart once).

### Codex

**User scope (all your projects):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git "$HOME/.agents/skills/kikita-create-nestjs-app"
```

**Repo scope (this project, and any subdirectory under it):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git .agents/skills/kikita-create-nestjs-app
```

Codex scans `.agents/skills` in the current directory and every parent up to the repo root. If a
newly installed or updated skill doesn't show up, restart Codex.

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
update mode instead of re-running the questionnaire: it `git pull`s its own install directory,
diffs `templates/.agents/` between the commit the project was scaffolded/last-updated from and
the current `HEAD`, and merges what changed into the project's `.agents/` files — never a blind
overwrite, since those files usually pick up project-specific edits after scaffolding. See
[`update.md`](./update.md) for the exact algorithm.

This works the same way whether you're driving Claude Code by hand or a fully agent-driven
("vibecoding") workflow that never opens the project directly — it's the same slash command
either way, no separate `-update` skill to install or remember.

## Scope

Single deployable app, not a monorepo/Nx workspace and not a distributed microservices topology
(multiple services/repos). A message broker, if chosen, wires a hybrid setup
(`app.connectMicroservice()`) inside the same single app — it never spins up a second service.
See [`templates/.agents/architecture/messaging.md`](./templates/.agents/architecture/messaging.md).

## Repo structure

```
SKILL.md          # skill entry point: mode detection, staged questionnaire + generation rules
plan.md           # step-by-step init sequence the skill follows
update.md         # step-by-step sequence for updating an already-scaffolded project
checklist.md      # post-init verification
templates/        # everything copied into the generated project
  AGENTS.md, CLAUDE.md, .gitignore, .editorconfig, .prettierrc, .prettierignore,
  .nvmrc, .vscode/extensions.json, .env.example, docker-compose.yml
  .agents/         # the documentation tree template, mirrors what gets generated
```

## License

[MIT](./LICENSE)
