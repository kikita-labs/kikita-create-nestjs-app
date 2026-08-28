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
- `.agents/file-change-review.md`
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
  layer — see `.agents/architecture/folder-structure.md`. Every file type (guard, interceptor,
  filter, decorator, middleware, exception, interface, entity, enum, constant, utility) has exactly one
  correct folder per that file's table — never invent an ad hoc top-level folder for something
  it already covers.
- A feature root is not an unlimited flat bucket: keep it to the module, primary transport/
  service, and feature-wide declarations; split a large feature into named capability folders at
  the six-production-file threshold. `src/core/` is only for app-wide singletons and
  infrastructure wrappers — a domain such as `legal` belongs under `src/modules/legal/`. Choose
  paths from responsibility and consumers, not from whichever role folders already exist or from
  a filename prefix; `@Global()` changes DI visibility, not domain ownership.
- After every source-file create/change/move, run `.agents/file-change-review.md` before reporting
  the task complete. A hand-written file over 400 non-blank, non-comment lines or a function over
  120 such lines is a blocking decomposition failure, not a style suggestion.
- Every dependency this project installs — Prisma, `nestjs-pino`, `nestjs-i18n`, the bot
  platform library, everything — is latest stable at install time, same rule as NestJS itself.
  A library's major-version API can change shape between scaffolds of this skill (Prisma has,
  more than once) — verify the installed major's actual current API/CLI flags against its own
  docs rather than trusting an example in this doc set to still be literally correct; the
  underlying *pattern* (driver adapter, config file requirement, etc.) is what's meant to carry
  forward, not necessarily the exact syntax.
- No reusable `interface`/`type`/`enum`/exported `const` left inline in a `.controller.ts`/
  `.service.ts`/`.dto.ts` — it moves to the matching `interfaces/`/`enums/`/`constants/`
  subfolder the moment a second file needs it. See
  `.agents/architecture/folder-structure.md`.
- Constructor-based dependency injection only — no property injection, no service locator. Not
  currently caught by lint (verify against `@darraghor/eslint-plugin-nestjs-typed`'s current
  rule set when the project's `eslint.config.js` is authored); treat as a review-blocking rule
  until/unless it is.
- Every DTO uses `class-validator`/`class-transformer` decorators. The global `ValidationPipe`
  (`whitelist`, `forbidNonWhitelisted`, `forbidUnknownValues`, `transform` all `true`) is wired
  in `main.ts` and must stay that way — never disable it per-route to "make validation easier".
  A nested-object/
  array-of-objects field needs both `@ValidateNested()` and `@Type(() => NestedDto)` — missing
  `@Type()` makes validation silently skip the nested value. See
  `.agents/code-style/dto-and-validation.md`.
- DTO reuse (`Update*` from `Create*`) goes through `PartialType`/`OmitType`/`PickType` imported
  from `@nestjs/swagger`, never `@nestjs/mapped-types` — ESLint-blocked
  (`no-restricted-imports`, see `.agents/testing-and-quality.md`), not just documented.
- Env/config values are validated by the Zod schema in `ConfigModule.forRoot({ validate })` —
  never read `process.env` directly in application code outside that schema file.
  ESLint-blocked (`no-restricted-syntax`, see `.agents/testing-and-quality.md`).
- Responses never leak a raw Prisma entity — return a DTO with `@Exclude()`/`@Expose()` on
  sensitive fields, **actually instantiated via
  `plainToInstance(..., { excludeExtraneousValues: true })`**, relying on the global
  `ClassSerializerInterceptor` wired in `main.ts` to strip it. A method whose return type merely
  claims the DTO type without
  an actual `plainToInstance` call does not get the exclusion — the interceptor only strips
  fields off real class instances, not plain objects with a matching TypeScript annotation. No
  competing serialization approach without an ADR. See
  `.agents/code-style/dto-and-validation.md`.
- Prisma is the only ORM; Postgres is the only database. Do not add a second ORM or database
  driver without an ADR (`.agents/decisions/README.md`).
- Path aliases (`@app/*`, `@generated/*`) are mandatory for cross-module imports. See
  `.agents/architecture/aliases-and-barrels.md`. A feature module never imports another
  feature's internals directly — only its exported public surface. See
  `.agents/architecture/module-boundaries.md`.
- No barrel `index.ts` files anywhere in `src/` — every import names the exact declaring file.
  Nest's own docs call barrels a same-directory circular-dependency trap; see
  `.agents/architecture/aliases-and-barrels.md`.
- CORS is always restricted to the `CORS_ORIGIN` env allowlist — never `*`.
- API routes are versioned (`/v1/...`) via Nest URI Versioning — see
  `.agents/architecture/transport-adapter.md`.
- `main.ts` always calls `app.enableShutdownHooks()` — without it, `PrismaService`'s
  `OnModuleDestroy` hook never fires on SIGTERM and connections leak on every container
  restart. Never remove this call.
- `GET /health/live` and `GET /health/ready` (`@nestjs/terminus`) are always present, not
  questionnaire-gated, and never merged into one route — liveness checks nothing external,
  readiness checks every wired dependency. See `.agents/core/health.md`. A global
  `PrismaExceptionFilter` maps Prisma constraint/not-found errors to the matching HTTP
  exception — a Prisma error must never surface as an unhandled 500. See
  `.agents/architecture/transport-adapter.md`'s Bootstrap wiring section.
- All application and bootstrap logs use `nestjs-pino`; production output is structured JSON,
  application code has no `console.*`, and secrets/raw exception objects are never logged.
  Classify expected versus unexpected failures, log unexpected failures once at their final
  boundary, and include only bounded error fields. See `.agents/core/logging.md`.
<!-- SCAFFOLD: keep the next two lines only if auth was chosen -->
- Auth follows the one fixed pattern in `.agents/core/auth.md` — short-lived access token,
  rotated refresh token in an httpOnly cookie, CSRF protection on the refresh route. Do not
  introduce an alternate auth strategy without an ADR.
- Passwords are hashed with `argon2id` (`argon2` package) — `bcrypt`/`bcryptjs` are
  ESLint-blocked (`no-restricted-imports`).
<!-- SCAFFOLD: keep the next two lines only if i18n was chosen -->
- Locale resolution differs by transport — REST uses `AcceptLanguageResolver`, a bot never has
  an `Accept-Language` header and resolves locale from the platform's own per-user locale field
  instead. See `.agents/core/i18n.md`.
- Every translation key exists in the fallback locale (`DEFAULT_LOCALE`) even if untranslated
  elsewhere — a missing key degrades to the fallback language, never an empty string.
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
