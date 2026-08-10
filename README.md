# kikita-create-nestjs-app

An agent skill that scaffolds a brand-new NestJS project (latest stable) — REST API, a bot on
any platform (Telegram, Discord, or another), or both in the same app — and generates a full
`.agents/` documentation tree alongside it, so any AI agent working in the project afterwards has
a complete, self-maintaining source of truth from commit one.

Packaged as an [Agent Plugin](https://agent-plugins.org) (spec v1.0.0) — a portable format
usable by any compatible client (Cursor, GitHub Copilot, ChatGPT/Codex, VS Code, Kiro, …),
not just Claude Code.

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
- REST branch: Swagger at `/docs`, URI versioning (`/v1/...`), env-driven CORS allowlist.
- Bot branch: generic Update-handler transport pattern, with concrete adapters for
  `nestjs-telegraf` (Telegram) and `necord` (Discord) — see
  [`templates/.agents/architecture/transport-adapter.md`](./skills/kikita-create-nestjs-app/templates/.agents/architecture/transport-adapter.md).
- A two-stage pre-init questionnaire (application type/platform first, then tests, auth, queue,
  cache, file uploads, messaging, TSDoc policy, git policy, package manager, git remote) drives
  which docs and config get generated — see `SKILL.md` for why it's staged, not one flat list.

## Install

This repo is an [Agent Plugin](https://agent-plugins.org): a `plugin.json` manifest at the
root plus a `skills/kikita-create-nestjs-app/` directory holding the actual
[Agent Skill](https://agent-plugins.org/specification). Any Agent-Plugins-compatible client
can load it straight from a clone of this repo.

### Agent-Plugins-compatible clients (Cursor, GitHub Copilot, ChatGPT/Codex, VS Code, Kiro, …)

Point the client's plugin install flow at this repo (clone URL or local path). The client
discovers `plugin.json`, then the skill under `skills/kikita-create-nestjs-app/`. Refer to
your client's own docs for the exact install command — the Agent Plugins spec defines the
package format, not a universal installer.

### Claude Code

Claude Code doesn't read the Agent Plugins format natively yet, so install the skill
subdirectory directly:

**Personal (all your projects):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git /tmp/kikita-nest-app && \
  cp -r /tmp/kikita-nest-app/skills/kikita-create-nestjs-app ~/.claude/skills/kikita-create-nestjs-app
```

**Project-scoped (this project only, committed to the repo):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git /tmp/kikita-nest-app && \
  cp -r /tmp/kikita-nest-app/skills/kikita-create-nestjs-app .claude/skills/kikita-create-nestjs-app
```

Claude Code picks up new/changed skills under `~/.claude/skills/` and `.claude/skills/` live,
within the current session — no restart needed, unless the top-level `.claude/skills/` directory
didn't exist yet when the session started (in that case restart once).

### Codex

**User scope (all your projects):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git /tmp/kikita-nest-app && \
  cp -r /tmp/kikita-nest-app/skills/kikita-create-nestjs-app "$HOME/.agents/skills/kikita-create-nestjs-app"
```

**Repo scope (this project, and any subdirectory under it):**

```sh
git clone https://github.com/kikita-labs/kikita-create-nestjs-app.git /tmp/kikita-nest-app && \
  cp -r /tmp/kikita-nest-app/skills/kikita-create-nestjs-app .agents/skills/kikita-create-nestjs-app
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
diffs `skills/kikita-create-nestjs-app/templates/.agents/` between the commit the project was
scaffolded/last-updated from and the current `HEAD`, and merges what changed into the project's
`.agents/` files — never a blind overwrite, since those files usually pick up project-specific
edits after scaffolding. See [`update.md`](./skills/kikita-create-nestjs-app/update.md) for the
exact algorithm. Note this requires a git-clone install (not a copy) so `<plugin-root>` has
history to diff against — see `update.md` section 1.

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
