# Init Plan

Execute in order. Do not reorder. Do not skip a step because it "seems unnecessary" — if a step
doesn't apply (e.g. no auth chosen), mark it skipped explicitly and move on.

1. **Ask the questionnaire** (`SKILL.md` section 1). Do not proceed until every answer is
   recorded.

2. **Scaffold the NestJS app** with the latest stable Nest CLI (`nest new`), using the chosen
   package manager (`--package-manager {{PACKAGE_MANAGER}}`; default `pnpm`). Delete the
   generated sample `app.controller.ts`/`app.service.ts`/their `.spec.ts` files — they're
   placeholder noise, not a real feature module.

3. **Wire Prisma + Postgres** (fixed default, no question asked):
   - `{{PACKAGE_MANAGER}} add @prisma/client` + `-D prisma`, `npx prisma init --datasource-provider postgresql`.
   - Point `DATABASE_URL` at the `docker-compose.yml` Postgres service (step 4).
   - Add a `PrismaService` under `src/core/prisma/` (extends `PrismaClient`, implements
     `OnModuleInit`/`OnModuleDestroy`) and a global `PrismaModule` exporting it — see
     `templates/.agents/core/README.md` for the registry entry to add.

4. **Write `docker-compose.yml`** (always generated, dev/test only):
   - Postgres service always present, env-driven credentials matching `.env.example`.
   - Add the Redis service only if BullMQ and/or caching was chosen (share one instance for
     both — don't spin up two Redis containers).
   - Add the RabbitMQ service only if messaging was chosen.
   - Copy `templates/docker-compose.yml`, deleting the `<!-- SCAFFOLD -->`-marked blocks that
     don't apply.

5. **Wire validation** (fixed default, no question asked):
   - `{{PACKAGE_MANAGER}} add class-validator class-transformer zod @nestjs/config`.
   - Global `ValidationPipe` in `main.ts`:
     `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`.
   - `ConfigModule.forRoot({ validate })` with a Zod schema validating every env var the
     project actually uses — start with `DATABASE_URL`, `PORT`, `CORS_ORIGIN`, extend per
     feature chosen below.

6. **Wire logging**: `{{PACKAGE_MANAGER}} add nestjs-pino pino-http`, `LoggerModule.forRoot()`
   in `AppModule`, replace Nest's bootstrap logger with the Pino one in `main.ts`
   (`bufferLogs: true` + `app.useLogger(app.get(Logger))`).

7. **Wire the transport layer(s)** per the application-type answer — see
   `templates/.agents/architecture/transport-adapter.md` for the full pattern:
   - **REST**: `{{PACKAGE_MANAGER}} add @nestjs/swagger`, enable URI versioning
     (`app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' })`), configure CORS
     from `CORS_ORIGIN` env, set up `SwaggerModule` at `/docs`.
   - **Bot**: install the platform library (`nestjs-telegraf` for Telegram, `necord` for
     Discord; for "another platform", install what the user named and hand-adapt the generic
     Update-handler pattern). Create `src/bot/bot.module.ts` + `src/bot/updates/`.
   - **Both**: do both of the above; `src/modules/` business logic is shared, only the thin
     transport layer differs (Controller vs Update handler calling the same service).

8. **If auth was chosen**, scaffold the fixed pattern from `templates/.agents/core/auth.md`:
   `@nestjs/jwt`, `@nestjs/passport`, `passport-jwt`, `argon2`, `cookie-parser`, `csrf-csrf`.
   Access token short-lived, returned in the response body. Refresh token httpOnly cookie
   scoped to `/auth/refresh`, rotated on every use (hash stored in `RefreshToken` Prisma
   model, previous hash invalidated). `RolesGuard` + a `@Roles()` decorator. Do not add
   session-based auth or an alternate token strategy — this is the one default.

9. **If background jobs were chosen**: `{{PACKAGE_MANAGER}} add @nestjs/bullmq bullmq`, wire
   `BullModule.forRoot()` against the Redis service from step 4, create one example queue module
   under `src/modules/` demonstrating the processor pattern.

10. **If caching was chosen**: `{{PACKAGE_MANAGER}} add @nestjs/cache-manager cache-manager @keyv/redis`,
    wire `CacheModule.registerAsync()` against the same Redis instance, document the cache-aside
    pattern and default TTL in `templates/.agents/core/cache.md`.

11. **If file uploads were chosen**: `{{PACKAGE_MANAGER}} add @nestjs/platform-express multer @aws-sdk/client-s3`,
    build the storage-adapter interface under `src/core/storage/` (local-disk implementation for
    dev, S3-compatible implementation for prod, selected by an env var), Multer configured with
    `memoryStorage()` and `limits` (`fileSize`, `files`), MIME-type whitelist in a custom pipe.

12. **If messaging was chosen**: `{{PACKAGE_MANAGER}} add @nestjs/microservices amqplib amqp-connection-manager`,
    wire `app.connectMicroservice({ transport: Transport.RMQ, options: {...} })` in `main.ts`
    alongside the existing HTTP/bot transport (hybrid app, not a separate service), add one
    example `@MessagePattern`/`@EventPattern` handler.

13. **Set up tooling**:
    - Copy `templates/.gitignore`, `templates/.editorconfig`, `templates/.prettierrc`,
      `templates/.prettierignore`, `templates/.vscode/extensions.json`, `templates/.env.example`
      into the project as-is (env-example gated blocks stripped per the questionnaire answers).
    - Copy `templates/.nvmrc`, replacing `{{NODE_VERSION}}` with the Node version the chosen
      Nest release actually requires — check, don't guess.
    - ESLint flat config: `@darraghor/eslint-plugin-nestjs-typed` recommended +
      `typescript-eslint` `strict-type-checked` + `eslint-plugin-simple-import-sort` +
      `@typescript-eslint/consistent-type-imports` + a restricted-import boundary rule, with
      `eslint-config-prettier` last. `ignores` covers `dist/`, `node_modules/`, `coverage/`,
      `generated/` (Prisma client output), lockfiles.
    - Wire `lint` / `format` / `format:check` scripts using `{{PACKAGE_MANAGER}}`.
    - Install and configure Husky + `lint-staged`, `"prepare": "husky"` in `package.json`:
      `pre-commit` runs `lint-staged` + the non-English content check; `pre-push` runs the full
      `lint` + `format:check` + test gate. Same responsibilities and `sh -e` gotcha as
      `kikita-create-angular-app` — see `templates/.agents/git-policy.md` and
      `templates/.agents/testing-and-quality.md`.
    - `git update-index --chmod=+x .husky/pre-commit .husky/pre-push` after writing the hooks.
    - Create the skeleton folders `src/core/`, `src/common/`, `src/modules/` (each with a
      barrel `index.ts` where it holds more than one file).

14. **If tests were chosen**, wire Jest (already ships with `nest new`) for unit and/or
    Supertest for e2e per the answer; if "both", also add Testcontainers
    (`@testcontainers/postgresql`) wired into the e2e Jest config to spin up a real Postgres
    per test run instead of mocking Prisma. Document the setup in the generated
    `.agents/testing-and-quality.md`.

15. **Generate the documentation tree** from `templates/`:
    - `CLAUDE.md`, `AGENTS.md` at project root.
    - `.agents/README.md` — flat index, kept in sync with whichever conditional files actually
      got generated.
    - `.agents/*.md` flat topic docs (workflow, git-policy, documentation, testing-and-quality,
      refactoring, progress — always include all of these) plus `agent-surface.md` only if
      mandatory TSDoc was chosen.
    - `.agents/code-style/` with its `README.md` hub + `imports.md`, `provider-structure.md`,
      `dto-and-validation.md`, `module-structure.md`.
    - `.agents/architecture/` with its `README.md` hub + `folder-structure.md`,
      `aliases-and-barrels.md`, `module-boundaries.md`, `transport-adapter.md`, and
      `messaging.md` only if messaging was chosen.
    - `.agents/shared/README.md` and `.agents/core/README.md` — both start with an empty
      registry table, plus `core/auth.md` / `core/queue.md` / `core/cache.md` / `core/storage.md`
      only for the features actually chosen.
    - `.agents/decisions/README.md` — always generated, starts with no ADR files.
    - Fill every `{{PLACEHOLDER}}` with the real questionnaire answer. Leave no placeholder text.
    - Update `AGENTS.md`'s "Must Read" list to only reference files that were actually generated.

16. **`git init`, wire remote if given one, first commit.**
    - `git init` if not already a repo.
    - If the questionnaire gave a remote URL: `git remote add origin <url>`. If no URL was
      given, skip — do not invent or guess a remote.
    - Commit following the generated `.agents/git-policy.md` (commit message rules, no AI
      attribution).
    - Only push if the git-policy answer authorizes it without asking; otherwise stop after the
      commit and ask before pushing.

17. **Run `checklist.md`.** Fix anything that fails before reporting completion to the user.
