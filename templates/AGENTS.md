# AGENTS.md

This repository contains {{PROJECT_NAME}}, a NestJS application ({{APP_TYPE}}).

This file is the mandatory entry point for every AI agent. Read it first, then read the linked
`.agents/*.md` files required by the task.

## Must Read

Always read:

- `.agents/README.md` — full map of everything under `.agents/`.
- `.agents/workflow.md`
- `.agents/git-policy.md`
- `.agents/documentation.md`
- `.agents/testing-and-quality.md`
- `.agents/code-style/README.md`
- `.agents/architecture/README.md`

<!-- SCAFFOLD: keep the next line only if mandatory TSDoc was chosen -->
- `.agents/agent-surface.md`
- `.agents/refactoring.md`

For provider or shared-utility work, also read:

- `.agents/shared/README.md`
- `.agents/core/README.md`

For a structural change (layer direction, transport strategy, messaging topology, versioning
strategy), also read:

- `.agents/decisions/README.md`

## Non-Negotiable Rules

- Latest stable NestJS only. Modules by feature (`src/modules/<feature>/`), not by technical
  layer — see `.agents/architecture/folder-structure.md`.
- Constructor-based dependency injection only — no property injection, no service locator.
- Every DTO uses `class-validator`/`class-transformer` decorators. The global `ValidationPipe`
  (`whitelist`, `forbidNonWhitelisted`, `transform` all `true`) is wired in `main.ts` and must
  stay that way — never disable it per-route to "make validation easier".
- DTO reuse (`Update*` from `Create*`) goes through `PartialType`/`OmitType`/`PickType` imported
  from `@nestjs/swagger`, never `@nestjs/mapped-types` — see
  `.agents/code-style/dto-and-validation.md`.
- Env/config values are validated by the Zod schema in `ConfigModule.forRoot({ validate })` —
  never read `process.env` directly in application code.
- Prisma is the only ORM; Postgres is the only database. Do not add a second ORM or database
  driver without an ADR (`.agents/decisions/README.md`).
- Path aliases are mandatory for cross-module imports. See
  `.agents/architecture/aliases-and-barrels.md`. A feature module never imports another
  feature's internals directly — only its exported public surface. See
  `.agents/architecture/module-boundaries.md`.
- CORS is always restricted to the `CORS_ORIGIN` env allowlist — never `*`.
- API routes are versioned (`/v1/...`) via Nest URI Versioning — see
  `.agents/architecture/transport-adapter.md`.
<!-- SCAFFOLD: keep the next line only if auth was chosen -->
- Auth follows the one fixed pattern in `.agents/core/auth.md` — short-lived access token,
  rotated refresh token in an httpOnly cookie, CSRF protection on the refresh route. Do not
  introduce an alternate auth strategy without an ADR.
- All tracked repository content is English-only, including TSDoc and comments. No Cyrillic,
  no mojibake.
- Never add `Co-authored-by`, `Generated-by`, AI attribution, or assistant attribution lines to
  commit messages. Never claim co-authorship for Claude, Codex, ChatGPT, or any other AI tool.
- Do not invent library APIs or behavior. If a spec or installed package doesn't cover what you
  need, stop and report the gap instead of guessing.
- Any change to a shared utility, core singleton, DTO convention, or module boundary must update
  the matching `.agents/` doc in the same change. See `.agents/documentation.md`.

## Source Of Truth

- `.agents/` for conventions and process.
- Installed package versions (`package.json`) and `prisma/schema.prisma` for actual API
  surface/data shape — never assume an API or a field exists without checking.
- `.agents/shared/README.md` and `.agents/core/README.md` for what's already built and reusable
  before building something new.
