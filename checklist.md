# Post-Init Checklist

Run through every item. Do not report the project as ready until every box that applies is
genuinely true — do not check a box you didn't verify.

## Setup

- [ ] Latest stable NestJS CLI used (`nest --version` matches current stable, not pinned old).
- [ ] Project builds (`{{PACKAGE_MANAGER}} run build`) with zero errors.
- [ ] Sample `app.controller.ts`/`app.service.ts` (and their specs) removed — not left as dead
      placeholder code.
- [ ] Project scaffolded with the chosen package manager (lockfile matches: exactly one of
      `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock`).

## Data layer

- [ ] Prisma + Postgres wired; `prisma/schema.prisma` present, `DATABASE_URL` in `.env.example`
      matches the `docker-compose.yml` Postgres service.
- [ ] `docker compose up -d` actually starts Postgres (and Redis/RabbitMQ if those features were
      chosen); `npx prisma migrate dev` runs clean against it.
- [ ] `PrismaService`/`PrismaModule` under `src/core/prisma/`, registered in `.agents/core/README.md`.
- [ ] `package.json` has `"postinstall": "prisma generate"` — a fresh
      `{{PACKAGE_MANAGER}} install` alone produces a working `@prisma/client` import, nobody has
      to run it by hand.

## Validation, logging, transport

- [ ] Global `ValidationPipe` in `main.ts` with `whitelist`, `forbidNonWhitelisted`, `transform`
      all `true`.
- [ ] `ConfigModule` validates env vars via a Zod schema — startup fails loudly on a missing var,
      not silently on first use.
- [ ] Every DTO field that's a nested object/array of objects has both `@ValidateNested()` and
      `@Type(() => NestedDto)` — spot-check by submitting an invalid nested value and confirming
      the request is actually rejected, not silently accepted.
- [ ] `nestjs-pino` wired; app boot logs are structured JSON, not the default Nest logger output.
- [ ] `main.ts` calls `app.enableShutdownHooks()`.
- [ ] Global `ClassSerializerInterceptor` wired in `main.ts`; a DTO with an `@Exclude()` field
      (e.g. a password hash) actually comes back stripped in a real response, not just present
      in the interceptor registration.
- [ ] Global `PrismaExceptionFilter` wired as `APP_FILTER`; triggering a unique-constraint
      violation returns a `409`, not an unhandled `500`.
- [ ] `GET /health/live` responds `200` and checks nothing external (verify it stays `200` even
      with the `docker-compose.yml` Postgres service stopped). `GET /health/ready` responds `200`
      normally and fails (`503`) when Postgres is stopped, recovering once it's back — see
      `.agents/core/health.md`.
- [ ] REST branch (if chosen): Swagger served at `/docs`, URI versioning active (`/v1/...` in
      route paths), CORS restricted to the `CORS_ORIGIN` env allowlist — never `*`, IP-keyed
      `ThrottlerGuard` wired and actually rejects a burst of requests past the limit.
- [ ] Bot branch (if chosen): platform library installed and connecting with a real (or
      placeholder, clearly marked) token from env; `src/bot/updates/` has at least one handler;
      throttler guard keyed by user/chat id, not IP.
- [ ] "Both" chosen: REST controller and bot update handler both call into the same
      `src/modules/*` service — no duplicated business logic between the two transports.

## Optional features (only if chosen)

- [ ] Auth: access token short-lived and returned in the response body (never in a cookie);
      refresh token httpOnly cookie scoped to `/auth/refresh`; rotation implemented (old hash
      invalidated on refresh); `csrf-csrf` wired on the refresh route; passwords hashed with
      `argon2id` (`bcrypt`/`bcryptjs` not in `package.json` dependencies at all); `RolesGuard`
      present.
- [ ] Background jobs: BullMQ wired against the Redis service, one example processor exists.
- [ ] Caching: `@nestjs/cache-manager` + `@keyv/redis` wired, cache-aside example present with an
      explicit TTL — not left unbounded.
- [ ] File uploads: storage adapter has both a local-disk and an S3-compatible implementation,
      selected by env var; Multer `limits` (size + count) and a MIME-type whitelist are enforced.
- [ ] Messaging: `app.connectMicroservice()` wired alongside the existing transport (same app,
      not a second service); at least one `@MessagePattern`/`@EventPattern` handler exists.
- [ ] Tests: Jest unit and/or Supertest e2e configured per the answer; if "both" was chosen,
      Testcontainers spins up a real Postgres for the e2e run — not mocked.

## Tooling

- [ ] `.gitignore` covers `node_modules`, `dist`, `coverage`, `generated/` (Prisma client
      output), env files, lockfiles of the *other* package managers, `.claude/`, `.codex/`.
- [ ] `.editorconfig`, `.prettierrc`, `.prettierignore`, `.vscode/extensions.json` present.
- [ ] `.nvmrc` present with the real Node version, not the `{{NODE_VERSION}}` placeholder.
- [ ] ESLint flat config present (`@darraghor/eslint-plugin-nestjs-typed` recommended +
      `typescript-eslint` `strict-type-checked` + `simple-import-sort` +
      `consistent-type-imports` + a restricted-import boundary rule, `eslint-config-prettier`
      last), lints with zero errors on the generated skeleton.
- [ ] The `no-restricted-imports` (`@nestjs/mapped-types`, `bcrypt`, `bcryptjs`) and
      `no-restricted-syntax` (`process.env` outside the config schema file) rules from
      `.agents/testing-and-quality.md`'s "Mechanically Enforced Rules" are actually present in
      `eslint.config.js` — confirm by writing a throwaway file that violates each and running
      lint, not just reading the config.
- [ ] `lint`, `format`, `format:check` scripts exist and run clean.
- [ ] `package.json` has `"prepare": "husky"`. Husky installed: `pre-commit` runs `lint-staged`
      + the non-English content check, `pre-push` runs the full lint + format + test gate.
      Verify both hooks actually fire (e.g. dry-run a commit).

## Documentation

- [ ] `CLAUDE.md` exists and only points to `AGENTS.md`.
- [ ] `AGENTS.md` "Must Read" list contains only files that actually exist — no dead links.
- [ ] `.agents/README.md` links only to files that actually exist — no dead links, no missing
      conditional files (auth, queue, cache, storage, messaging, agent-surface).
- [ ] Every file under `.agents/` has all `{{PLACEHOLDER}}` tokens replaced with real values.
- [ ] `.agents/code-style/README.md` links to every file in `.agents/code-style/`.
- [ ] `.agents/architecture/README.md` links to every file in `.agents/architecture/`.
- [ ] `.agents/shared/README.md` and `.agents/core/README.md` exist even if empty, each with
      instructions for how to register a new entry.
- [ ] `.agents/decisions/README.md` exists with the ADR trigger list and format.
- [ ] `.agents/agent-surface.md` present only if mandatory TSDoc was chosen.
- [ ] `.agents/documentation.md` (the "how to write/maintain docs" master file) exists and is
      linked from `AGENTS.md`.
- [ ] No Cyrillic or mojibake in any tracked file, including TSDoc.

## Git

- [ ] `.agents/git-policy.md` reflects the questionnaire's ask-before-push answer correctly.
- [ ] `git remote` set to the URL the user gave, if one was given; not invented, not left unset
      if one was provided.
- [ ] First commit made, message has no AI attribution / co-authorship lines.
- [ ] `git status` clean after the commit.

## Final

- [ ] Re-read `AGENTS.md` top to bottom as if you were a fresh agent — does it actually orient
      you correctly with no missing context?
