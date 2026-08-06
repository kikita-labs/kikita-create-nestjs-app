---
name: kikita-create-nestjs-app
description: Scaffold a new NestJS project (latest stable) — REST API and/or bot (any platform) — with a full .agents/ documentation tree, code style, and git policy pre-wired. Use when the user asks to init/bootstrap/create a new NestJS app/API/bot, or invokes /kikita-create-nestjs-app in an empty or near-empty directory.
---

# kikita-create-nestjs-app

Bootstraps a new NestJS project and generates its `AGENTS.md` / `.agents/` documentation tree so
any AI agent (Claude Code, Codex, etc.) working in the project afterwards has a complete,
self-maintaining source of truth.

Follow `plan.md` step by step. Do not skip the questionnaire. When done, run through
`checklist.md` before telling the user it's finished.

## 0. Preconditions

- Confirm the working directory is empty or the user explicitly wants to init here.
- Never run this against a directory that already has an unrelated project without asking first.

## 1. Questionnaire (always ask before touching the filesystem)

Ask in two stages, not as 11 questions dumped in one shot — the first answer decides which of
the later questions are even relevant, so asking them all upfront means presenting a bot-only
user with an "auth for your REST API" question that doesn't apply to them.

**Stage 1 — the branching question, alone:**

1. **Application type**: REST API, bot, or both in the same app?
   - If bot (or both): which platform? Telegram (`nestjs-telegraf`), Discord (`necord`), or
     another platform (name the library — the generic bot transport pattern in
     `architecture/transport-adapter.md` adapts to it, but the concrete adapter code needs to be
     written by hand for anything outside Telegram/Discord).

**Stage 2 — everything else, batched (question 3 only asked if stage 1 answered REST or
"both"; every other question below applies regardless of application type):**

2. **Tests**: none, or unit / e2e (Supertest) / both? "Both" also wires Testcontainers for
   integration tests that hit a real Postgres instance instead of mocks.
3. **Auth** (skip entirely if stage 1 was bot-only): needed or not? A "yes" scaffolds one fixed
   battle-tested pattern, not a menu — see `core/auth.md`'s scaffold block: short-lived access
   token (5–15 min, never in a cookie) + refresh token in an httpOnly cookie scoped to
   `/auth/refresh` + rotation (single-use, hashed in DB) + `csrf-csrf` on the refresh endpoint +
   `argon2id` password hashing + a `RolesGuard`. Do not offer alternatives (sessions, bare JWT
   without rotation) — this is the one default.
4. **Background jobs**: BullMQ (Redis-backed queues) or not?
5. **Caching**: `@nestjs/cache-manager` + `@keyv/redis` (cache-aside) or not? Default recommendation
   is **no** — add it when there's a real performance need, not speculatively on every CRUD
   endpoint.
6. **File uploads**: needed or not? If yes, no further sub-question — the storage vendor
   (local disk in dev, any S3-compatible bucket in prod: AWS S3, MinIO, R2, Spaces) is an env
   variable, not a scaffold-time choice.
7. **Async messaging / inter-service events**: needed or not? If yes, no broker sub-question
   either — RabbitMQ is the fixed default (task queues, routing, DLQ cover the overwhelming
   majority of cases). `architecture/messaging.md` documents Kafka as a later migration path for
   event-streaming/replay/extreme-throughput needs, not a scaffold-time option.
8. **JSDoc/TSDoc on public API**: enforce mandatory doc comments on every exported symbol, or
   skip it? Drives whether `.agents/agent-surface.md` is generated (recommended default: yes).
9. **Git policy**: may the agent commit and push without asking each time, or must every
   commit/push be confirmed?
10. **Package manager**: npm, pnpm, or yarn? Default recommendation: pnpm.
11. **Git remote**: does the user already have a repo URL to push to? If yes, record it —
    `git remote add origin <url>` runs right after `git init` (see `plan.md`). If no URL is
    given, skip this; the user wires the remote later themselves.

Record every answer — they drive both scaffolding and which doc files get generated. Never
silently assume a default beyond what's explicitly fixed above; if the user skips a question,
ask again for that one. This skill targets a single NestJS project, not a monorepo/Nx workspace
and not a distributed microservices topology (multiple deployable services/repos) — if the user
wants either, say this skill doesn't cover that and stop rather than improvising. A message
broker (see question 7) only wires a hybrid app (`app.connectMicroservice()` inside the same
single app) — it never spins up a second service.

Fixed defaults — **never** ask about these, they're locked by design:

- **ORM/DB**: Prisma + Postgres. No TypeORM (not recommended for new projects), no Drizzle (niche
  perf/edge pick), no NoSQL/MongoDB branch in v1 of this skill.
- **Validation**: `class-validator` + `class-transformer` on the HTTP layer, global
  `ValidationPipe` (`whitelist: true, forbidNonWhitelisted: true, transform: true`) wired in
  `main.ts` unconditionally. Zod for env/config validation (`@nestjs/config` + `validate`).
  DTO reuse via `PartialType`/`OmitType`/`PickType` imported from `@nestjs/swagger` (not
  `@nestjs/mapped-types` — see the gotcha in `code-style/dto-and-validation.md`).
- **Swagger/OpenAPI**: always wired for the REST branch.
- **CORS**: always configured in `main.ts` via an env-driven origin allowlist, never `*`.
- **API versioning**: Nest URI Versioning (`/v1/...`), fixed in `architecture/transport-adapter.md`.
- **Logging**: `nestjs-pino`, always — structured JSON logs, no plain `Logger` option offered.
- **docker-compose.yml**: always generated (dev/test only, never referenced by prod deploy) —
  Postgres always present; Redis added only if BullMQ and/or caching was chosen (one shared
  instance for both); RabbitMQ added only if messaging was chosen.

## 2. Generate

Follow `plan.md`. Copy files from `templates/` into the target project, including the dotfiles
(`.gitignore`, `.editorconfig`, `.prettierrc`, `.prettierignore`, `.nvmrc`,
`.vscode/extensions.json`, `.env.example`, `docker-compose.yml`).

Two different things happen with questionnaire answers, don't conflate them:

- **Text placeholders** — find-and-replace every `{{TOKEN}}` with the real value, leave none
  behind: `{{PROJECT_NAME}}`, `{{APP_TYPE}}`, `{{BOT_PLATFORM}}`, `{{TESTS}}`, `{{GIT_POLICY}}`,
  `{{PACKAGE_MANAGER}}`, `{{NODE_VERSION}}`, `{{DATE}}`.
- **Inclusion gates** — application type, bot platform, tests, auth, queue, cache, storage,
  messaging, and mandatory-TSDoc answers don't fill a placeholder; they decide whether a whole
  file (or a `<!-- SCAFFOLD -->`-marked block inside one) is copied at all. A "no" answer means
  the file/block is deleted, not filled with an empty string. Gated files must still be linked
  from `AGENTS.md` / the relevant README when kept, and their links removed when skipped.

## 3. Verify

Run `checklist.md` in full before reporting success.

## Notes on documentation structure (read once, then follow templates/ literally)

- `CLAUDE.md` is always a one-line stub pointing to `AGENTS.md`.
- `AGENTS.md` is the mandatory entry point: a short "Must Read" list plus non-negotiable rules,
  at the project root.
- `.agents/README.md` is a flat index of everything under `.agents/` — keep it in sync whenever a
  conditional file (auth, queue, cache, storage, messaging, agent-surface) is added or skipped.
- Topics that are genuinely one short doc stay flat in `.agents/*.md` (workflow, git-policy,
  documentation, testing-and-quality, agent-surface, refactoring, progress).
- Topics that fan out into several docs, or per-feature registries, get a subfolder with its own
  `README.md` hub: `.agents/code-style/`, `.agents/architecture/`, `.agents/shared/`,
  `.agents/core/`, `.agents/decisions/`.
- `.agents/shared/README.md` registers `src/common/` (framework-agnostic utilities — zero
  `@nestjs/*` imports — plus generic pipes/filters/interceptors/decorators).
  `.agents/core/README.md` registers `src/core/` app-wide singletons (auth, Prisma client
  provider, logger, queue, cache, storage — each with its own conditional doc file when that
  feature was chosen).
- `.agents/decisions/README.md` explains when a short ADR is required (layer direction, message
  broker migration, versioning strategy change) — always generated, starts with no ADR files.
- All tracked file content — including TSDoc — is English only. No Cyrillic, no mojibake.
- All docs in `.agents/` must read like `kikita-create-angular-app`'s templates: imperative,
  short, example-backed, ending in a review/verification checklist.
