# Init Plan

Execute in order. Do not reorder. Do not skip a step because it "seems unnecessary" — if a step
doesn't apply (e.g. no auth chosen), mark it skipped explicitly and move on.

**Before writing any file in steps 2–16, open the specific `templates/.agents/**/*.md` file that
step cites and re-read it — don't rely on having read it earlier in the conversation or on
general NestJS knowledge.** `.agents/` doesn't exist in the target project yet at this point (it's
only generated in step 17), so the templates under this skill's own directory are the only source
of truth available while writing code — code written from memory of the questionnaire drifts from
`folder-structure.md`'s file-type table, `code-style/imports.md`'s group order, and each
`core/*.md`'s exact file layout in ways a later pass rarely catches. In particular: never invent a
file suffix that isn't in `folder-structure.md`'s file-type table (no `*.types.ts` — split into
`*.constant.ts`/`*.interface.ts` per that table), and never place a `core/*.md`-documented
singleton (auth, queue, cache, storage, i18n) under `src/modules/` — every one of those belongs
under `src/core/<name>/`, listed in `core/README.md`'s registry, even when the step text below
doesn't repeat the full path. Conversely, never put a business/domain feature under `src/core/`
just because it has many providers; use `src/modules/<feature>/` and split large features into
named capability folders per `folder-structure.md`.

"Feature-based" does not mean "one flat folder per feature." Keep a feature root for its module,
primary transport/service, and feature-wide declarations. Once it would exceed six production
`.ts` files, or once it contains two distinct capabilities, create named child folders and keep
their providers, clients, builders, state, DTOs, and tests together. Register them in the owning
feature module; do not create generic `services/`, `controllers/`, `utils/`, or `misc/` buckets.
Before writing a feature, make a short responsibility inventory: capability, role, consumers,
visibility, and target path for each file. Do not treat the existing folder list as an architecture
or use `@Global()` as a reason to place domain code under `src/core/`.

Before every source-file create/change/move in these steps, also re-read
`templates/.agents/file-change-review.md`, write its ownership/consumer/path inventory, and run
its gate immediately after that file is written. A file over 400 non-blank, non-comment lines or a
function over 120 such lines must be split before the scaffold is reported complete.

When a step creates or changes logging, exception, filter, middleware, bot/event, or job-boundary
code, also read `templates/.agents/core/logging.md` before writing it. Its error taxonomy and
redaction rules apply to every transport, not only to `src/core/logger/`.

1. **Ask the questionnaire** (`SKILL.md` section 1). Do not proceed until every answer is
   recorded.

2. **Scaffold the NestJS app** with the latest stable Nest CLI (`nest new`), using the chosen
   package manager (`--package-manager {{PACKAGE_MANAGER}}`; default `pnpm`). Delete the
   generated sample `app.controller.ts`/`app.service.ts`/their `.spec.ts` files — they're
   placeholder noise, not a real feature module.
   - **Nest CLI slugifies the project name to kebab-case** regardless of what's typed —
     `nest new botV2` silently produces a `bot-v2/` directory, not `botV2/`. If the target
     directory name must match something specific (a monorepo's `apps/<exact-name>` convention,
     an existing sibling app's naming), check the generated folder name immediately after this
     step and rename it before continuing — don't discover the mismatch later.

3. **Wire Prisma + Postgres — skip this entire step if bot-only and the questionnaire answer
   was "pure client to an existing backend"** (`SKILL.md` section 1's bot sub-question). In
   that case: no `@prisma/client`/`prisma` install, no `schema.prisma`, no `PrismaService`/
   `PrismaModule`, no Postgres service in `docker-compose.yml` (step 4), no `DATABASE_URL`,
   no `@generated/*` path alias (step 15), no `PrismaHealthIndicator` (step 7), no
   Testcontainers (step 16), no `PrismaExceptionFilter` (step 7). This app talks to its data
   exclusively through the existing backend's REST/WS API — treat it the same as any other
   external HTTP dependency. Otherwise (REST, "both", or bot-only "owns its data"), fixed
   default, no question asked. Prisma's CLI/client API has
   changed shape across majors more than once — verify the installed major's actual API against
   its current docs before following this step literally; the specifics below are current for
   Prisma 7 and will need re-checking again whenever the "latest stable" moves past it:
   - `{{PACKAGE_MANAGER}} add @prisma/client @prisma/adapter-pg` + `-D prisma dotenv`,
     `npx prisma init --datasource-provider postgresql`.
   - `prisma init` generates `prisma.config.ts` at the project root (Prisma 7+) — this file is
     required for `prisma migrate`/`generate` to run at all, don't delete it thinking it's
     scaffold noise. It legitimately reads `process.env` directly (needs a
     `no-restricted-syntax` override, see step 15) and needs the `dotenv` package to load
     `.env` before Prisma CLI commands run.
   - **`prisma init` also auto-installs its own agent-skill scaffolding**
     (`.agents/skills/`, `.windsurf/skills/`, `skills-lock.json`, `.claude/skills/prisma-*`) —
     this collides with this project's own `.agents/` documentation tree. Detect and delete
     whatever `prisma init` added under those paths right after running it, before continuing.
   - **No inline datasource URL** in `schema.prisma`'s `datasource` block (Prisma 7 rejects
     `url = env("DATABASE_URL")` there with `P1012`) — the connection string is passed to
     `PrismaClient`'s constructor via a driver adapter instead:
     `new PrismaClient({ adapter: new PrismaPg({ connectionString: env.DATABASE_URL }) })`.
   - In the `generator client` block, set `moduleFormat = "cjs"` explicitly. The current default
     generator emits ESM (`import.meta.url`), which breaks under Jest/ts-jest's CommonJS
     runtime — if tests were chosen (step 16), this is not optional. Even with `cjs`, the
     generated client's own internal imports keep `.js` extensions (NodeNext style) — Jest needs
     a `moduleNameMapper` entry stripping them
     (`{ "^(\\.{1,2}/.*)\\.js$": "$1" }`) in both `jest.config` files (unit and e2e) if tests
     were chosen.
   - Point `DATABASE_URL` at the `docker-compose.yml` Postgres service (step 4).
   - Add a `PrismaService` under `src/core/prisma/` (wraps `PrismaClient` constructed with the
     driver adapter above, implements `OnModuleInit`/`OnModuleDestroy`) and a global
     `PrismaModule` exporting it — see `templates/.agents/core/README.md` for the registry entry
     to add.
   - Add `"postinstall": "prisma generate"` to `package.json` scripts. The generated client
     (`generated/`) is gitignored — without this script, every fresh clone or CI run fails to
     compile on the first `@prisma/client` import until someone remembers to run it by hand.

4. **Write `docker-compose.yml`** (always generated, dev/test only):
   - Postgres service present whenever step 3 wasn't skipped, env-driven credentials matching
     `.env.example`. A bot-only pure-client app (step 3 skipped) gets no Postgres service here —
     it has no database to run one for.
   - Add the Redis service only if BullMQ and/or caching was chosen (share one instance for
     both — don't spin up two Redis containers).
   - Add the RabbitMQ service only if messaging was chosen.
   - Copy `templates/docker-compose.yml`, deleting the `# SCAFFOLD`-marked blocks that don't
     apply.

5. **Wire validation** (fixed default, no question asked):
   - `{{PACKAGE_MANAGER}} add class-validator class-transformer zod @nestjs/config`.
   - Global `ValidationPipe` in `main.ts`:
     `{ whitelist: true, forbidNonWhitelisted: true, forbidUnknownValues: true, transform: true }`.
   - `ConfigModule.forRoot({ validate })` with a Zod schema validating every env var the
     project actually uses — start with `DATABASE_URL`, `PORT`, `CORS_ORIGIN`, extend per
     feature chosen below.
   - Every DTO with a nested object/array-of-objects field adds `@ValidateNested()` +
     `@Type(() => NestedDto)` (from `class-transformer`) on that field — without `@Type()`,
     `class-transformer` can't instantiate the nested class and `class-validator` silently skips
     validating it. See `templates/.agents/code-style/dto-and-validation.md`.

6. **Wire logging**: `{{PACKAGE_MANAGER}} add nestjs-pino pino-http`. Same as every other core
   singleton (Prisma, Health, Auth, Queue/Cache/Storage, i18n) — the `forRootAsync()` config
   lives in its own `src/core/logger/logger.module.ts` wrapper, not inlined directly in
   `AppModule`'s `imports` array. Configure production JSON/stdout and development pretty output,
   redact authorization/cookie/set-cookie paths and project-specific secrets, and keep request
   bodies disabled by default. For HTTP, generate or validate one request ID at the boundary and
   pass that same value to `pino-http`; do not duplicate request-ID algorithms in separate
   middleware and logger configuration. Replace Nest's bootstrap logger with the Pino one in
   `main.ts` (`bufferLogs: true` + `app.useLogger(app.get(Logger))`, imported straight from
   `nestjs-pino` — that import is unaffected by the wrapper). The mandatory error classification,
   catch ownership, redaction, and correlation policy lives in `templates/.agents/core/logging.md`.

7. **Wire the app-wide bootstrap concerns** (fixed defaults, always on, regardless of app
   type) — see `templates/.agents/architecture/transport-adapter.md`'s "Bootstrap wiring"
   section for the full `main.ts` shape:
   - `app.enableShutdownHooks()` — without this, Nest never calls `OnModuleDestroy` on
     SIGTERM/SIGINT, so `PrismaService`'s connection-close hook from step 3 silently never
     fires in a container that gets stopped/restarted.
   - Global `ClassSerializerInterceptor`
     (`app.useGlobalInterceptors(new ClassSerializerInterceptor(app.get(Reflector)))`) — the
     fixed default for response shaping: DTOs/entities use `@Exclude()` on fields that must
     never leave the transport boundary (password hashes, internal flags), and the interceptor
     strips them automatically.
     Do not return a raw Prisma entity from a controller/update handler; do not invent a second
     serialization approach.
   - `{{PACKAGE_MANAGER}} add @nestjs/terminus`, wire a `HealthModule` with **two** routes —
     `GET /health/live` (checks nothing external, only "is the process responsive") and
     `GET /health/ready` (checks Prisma + any chosen Redis/RabbitMQ dependency — or, if step 3
     was skipped for a bot-only pure-client app, checks the existing backend's own health/API
     endpoint instead via a custom `HttpHealthIndicator`-based indicator; a bot-only readiness
     check must never come back empty just because it has no database) — never a single
     merged `GET /health`. See `templates/.agents/core/health.md` for why liveness must never
     depend on an external service. Always generated, not questionnaire-gated.
   - **If step 3 wasn't skipped**: a global `PrismaExceptionFilter` under `src/common/filters/`
     mapping `PrismaClientKnownRequestError` codes to the matching Nest HTTP exception (`P2002`
     unique-constraint → `ConflictException`, `P2025` record-not-found →
     `NotFoundException`, etc.) — without it, a Prisma constraint violation surfaces as an
     unhandled 500 instead of the correct 4xx. Registered as an `APP_FILTER` provider in
     `AppModule` (see `templates/.agents/code-style/module-structure.md`), **not**
     `app.useGlobalFilters()` in `main.ts`. A bot-only pure-client app has no Prisma, so this
     filter doesn't apply — its own upstream-API error mapping (if any) is a project-specific
     concern, not this fixed default.
   - Error responses use Nest's default `HttpException` JSON shape (`statusCode`, `message`,
     `error`) for the simple REST baseline — no accidental custom envelope wrapper. If a separate
     web client, bot, worker, or service consumes the response, define a documented stable error
     contract with `errorCode`, a safe message, allowlisted details, and a correlation ID as
     described in `templates/.agents/core/logging.md`; do not expose raw Prisma/provider/error
     metadata merely to make transports look alike. The Prisma exception filter's whole job is
     making known Prisma errors end up as safe `HttpException` subclasses, not inventing a second
     format or a generic unclassified 500.

8. **Wire the transport layer(s)** per the application-type answer — see
   `templates/.agents/architecture/transport-adapter.md` for the full pattern:
   - **REST**: `{{PACKAGE_MANAGER}} add @nestjs/swagger @nestjs/throttler`, enable URI
     versioning (`app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' })`),
     configure CORS from `CORS_ORIGIN` env, set up `SwaggerModule` at `/docs`, wire
     `ThrottlerModule.forRoot()` (IP-keyed default) plus a `ThrottlerGuard` registered as an
     `APP_GUARD` provider in `AppModule` — not `app.useGlobalGuards()` in `main.ts`.
   - **Bot**: install the platform library (`nestjs-telegraf` for Telegram, `necord` for
     Discord; for "another platform", install what the user named and hand-adapt the generic
     Update-handler pattern) plus `@nestjs/throttler` if not already added by the REST branch.
     **Verify the platform library's current `peerDependencies` against the exact version being
     installed before treating the pair as compatible** — e.g. `necord`'s pinned
     `discord-api-types` range vs the `discord.js` version actually resolved; an unmet-peer
     warning for a transitive type-only package is common and usually harmless, but check the
     library's own changelog/issues for that specific pair rather than assuming so silently
     (same caveat this plan already applies to Prisma's API churn in step 3).
     Create `src/bot/bot.module.ts` + `src/bot/updates/`, with a custom `getTracker()` on the
     throttler guard keyed by the platform's user/chat id instead of IP.
     **Before registering the throttler guard globally as an `APP_GUARD`, verify whether the
     chosen bot framework fires global guards/interceptors/filters once per actual user
     action or once per registered listener bound to that event type.** Confirmed for Necord:
     a global guard runs once per listener, not once per Discord interaction — with multiple
     listeners bound to the same event this produces duplicate throttle checks and, if the
     guard itself responds on rejection, duplicate replies. If the framework behaves this way,
     scope the guard per-command-class (`@UseGuards(BotThrottlerGuard)` on each update handler,
     as `architecture/transport-adapter.md` already documents) instead of registering it
     app-wide — the REST branch's "always global" default does not transfer to bot frameworks
     unchecked.
   - **Both**: do both of the above; `src/modules/` business logic is shared, only the thin
     transport layer differs (Controller vs Update handler calling the same service). One
     shared `@nestjs/throttler` install, two guard configurations (IP-keyed for REST routes,
     user/chat-id-keyed for bot handlers).

9. **If auth was chosen**, scaffold the fixed pattern from `templates/.agents/core/auth.md`
   **under `src/core/auth/`** — auth is an app-wide singleton like Prisma/Health, never a
   `src/modules/*` feature, even though it has a controller and DTOs the way a feature does; see
   `folder-structure.md`'s scaffold tree and `core/README.md`'s registry for the exact layout
   (`auth.controller.ts`, `auth.service.ts`, `auth.module.ts` at the root, plus `guards/`,
   `strategies/`, `decorators/`, and `dto/` subfolders). Keep additional auth capabilities in
   named child folders once the feature-layout threshold is reached; do not let auth become a
   flat pile of unrelated providers. Install `@nestjs/jwt`, `@nestjs/passport`, `passport-jwt`, `argon2`,
   `cookie-parser`, `csrf-csrf`. Access token short-lived, returned in the response body. Refresh
   token httpOnly cookie scoped to `/auth/refresh`, rotated on every use (hash stored in
   `RefreshToken` Prisma model, previous hash invalidated). `RolesGuard` + a `@Roles()` decorator.
   Do not add session-based auth, `bcrypt`, or an alternate token strategy — this is the one
   default. Add `app.use(cookieParser())` and `csrf-csrf`'s `doubleCsrfProtection` (scoped to
   `/v1/auth/refresh` only) to the bootstrap wiring from step 7 — `cookieParser()` must run
   before any guard/middleware that reads `req.cookies`, including the CSRF check itself.

10. **If background jobs were chosen**: `{{PACKAGE_MANAGER}} add @nestjs/bullmq bullmq`, wire
    `BullModule.forRoot()` against the Redis service from step 4, create one example queue
    module under `src/modules/` demonstrating the processor pattern.

11. **If caching was chosen**: `{{PACKAGE_MANAGER}} add @nestjs/cache-manager cache-manager @keyv/redis`,
    wire `CacheModule.registerAsync()` against the same Redis instance, document the cache-aside
    pattern and default TTL in `templates/.agents/core/cache.md`.

12. **If file uploads were chosen**: `{{PACKAGE_MANAGER}} add @nestjs/platform-express multer @aws-sdk/client-s3`,
    build the storage adapter under `src/core/storage/` exactly as `core/storage.md` names it —
    `storage.interface.ts` (`StorageAdapter` interface), `local-storage.adapter.ts`
    (`LocalStorageAdapter`), `s3-storage.adapter.ts` (`S3StorageAdapter`), `storage.module.ts`.
    The `.adapter.ts` suffix is deliberate (matches `folder-structure.md`'s `Adapter` row) —
    don't rename to `.service.ts`/`*Service`, even though it's a
    `@Injectable()` like every other provider. Multer configured with `memoryStorage()` and
    `limits` (`fileSize`, `files`), MIME-type whitelist in a custom pipe.

13. **If messaging was chosen**: `{{PACKAGE_MANAGER}} add @nestjs/microservices amqplib amqp-connection-manager`,
    wire `app.connectMicroservice({ transport: Transport.RMQ, options: {...} })` in `main.ts`
    alongside the existing HTTP/bot transport (hybrid app, not a separate service), add one
    example `@MessagePattern`/`@EventPattern` handler.

14. **If i18n was chosen**: `{{PACKAGE_MANAGER}} add nestjs-i18n`, create `src/i18n/en/` with at
    least one namespace file, wire `I18nModule.forRootAsync()` under `src/core/i18n/` with
    `AcceptLanguageResolver` (REST) and `fallbackLanguage` from `DEFAULT_LOCALE` env. If REST or
    both: switch every `class-validator` decorator's `message` option to
    `i18nValidationMessage()`, add `I18nValidationExceptionFilter` as another `APP_FILTER`
    provider in `AppModule`. If bot or both: install the platform-specific integration
    (`nestjs-telegraf-i18n` for Telegram, `@necord/localization` for Discord — **verify this
    package actually exists, is current, and is what the platform's real docs recommend before
    installing it; don't treat a named package here as fact without checking**, same caveat this
    plan applies to Prisma's API in step 3; for another
    platform/raw `discord.js`, resolve the platform's per-user locale field by hand — see
    `templates/.agents/core/i18n.md`). If no verified package exists for the chosen platform, an
    explicit `{lang}` argument threaded through every translation call is an acceptable
    fallback — resolvers like `AcceptLanguageResolver` are HTTP-request-shaped and don't apply
    to a bot context anyway.

15. **Set up tooling**:
    - Copy `templates/.gitignore`, `templates/.gitattributes`, `templates/.editorconfig`,
      `templates/.prettierrc`, `templates/.prettierignore`, `templates/.vscode/extensions.json`,
      `templates/.env.example` into the project as-is (env-example gated blocks stripped per the
      questionnaire answers).
    - Copy `templates/.nvmrc`, replacing `{{NODE_VERSION}}` with the Node version the chosen
      Nest release actually requires — check, don't guess.
    - **If `{{PACKAGE_MANAGER}}` is pnpm**: current pnpm versions silently skip `postinstall`
      scripts for dependencies with native builds (`argon2` if auth was chosen, `@prisma/engines`
      transitively, and others) unless explicitly approved. Either run
      `pnpm approve-builds --all` once during scaffolding, or add an `onlyBuiltDependencies` list
      to **`pnpm-workspace.yaml`** at the project root (not `package.json`'s `pnpm` field — pnpm
      stopped reading that location). Skipping this step produces packages that silently don't
      work (`argon2` falls back to a pure-JS shim or errors at runtime) with no install-time
      error pointing at the cause.
    - **Wire `@app/*` path alias** end to end (and `@generated/*` too, **unless step 3 was
      skipped** — a bot-only pure-client app has no `generated/` Prisma output to map, so that
      half of the alias subsystem doesn't apply) —
      `architecture/aliases-and-barrels.md` declares them mandatory, so this subsystem has to
      actually exist, not just be assumed:
      - `tsconfig.json` `compilerOptions.paths`: `"@app/*": ["src/*"]` and, if Prisma was wired,
        `"@generated/*": ["generated/*"]` (the Prisma client output lives outside `src/`, so it
        needs its own mapping — see `aliases-and-barrels.md`).
      - TypeScript's `paths` is a type-checking-only feature — it does not rewrite import paths
        in compiled output. Add `tsc-alias` as a dev dependency and run it right after `tsc` in
        the `build` script (`tsc && tsc-alias`), so compiled `dist/` output has real relative
        paths instead of unresolved `@app/...`/`@generated/...` imports.
      - Add matching `moduleNameMapper` entries
        (`"^@app/(.*)$": "<rootDir>/src/$1"`, `"^@generated/(.*)$": "<rootDir>/generated/$1"`) to
        **every** Jest config that exists — unit and e2e are commonly separate config files/
        projects in a Nest scaffold, both need the mapping independently, not just one.
    - ESLint flat config: `@darraghor/eslint-plugin-nestjs-typed` recommended +
      `typescript-eslint` `strict-type-checked` + `eslint-plugin-simple-import-sort` +
      `@typescript-eslint/consistent-type-imports` + the restricted-import boundary patterns
      from `templates/.agents/architecture/README.md`'s "Automated boundary checks" section
      (these two docs describe the same config from different angles — both sets of rules go
      into the one file, not just whichever was read most recently), with `eslint-config-prettier`
      last. `ignores` covers `dist/`, `node_modules/`, `coverage/`, `generated/` (Prisma client
      output), lockfiles. See `templates/.agents/testing-and-quality.md`'s "Mechanically Enforced
      Rules" section for the exact `no-restricted-imports`/`no-restricted-syntax` blocks this
      config must include — several `AGENTS.md` rules (no `@nestjs/mapped-types`, no `bcrypt`, no
      direct `process.env`) are only real if this config actually has them, not just documented
      prose. Also see that same section for rules from `@darraghor/eslint-plugin-nestjs-typed`'s
      recommended set that need an override at scaffold time, not after they cause friction.
    - Wire `lint` / `format` / `format:check` scripts using `{{PACKAGE_MANAGER}}`.
    - Install and configure Husky + `lint-staged`, `"prepare": "husky"` in `package.json`:
      `pre-commit` runs `lint-staged` + the non-English content check; `pre-push` runs the full
      `lint` + `format:check` + test gate. Same responsibilities and `sh -e` gotcha as
      `kikita-create-angular-app` — see `templates/.agents/git-policy.md` and
      `templates/.agents/testing-and-quality.md`.
    - `git update-index --chmod=+x .husky/pre-commit .husky/pre-push` after writing the hooks.
    - Create the skeleton folders `src/core/`, `src/common/`, `src/modules/`. No barrel
      `index.ts` in any of them — see `architecture/aliases-and-barrels.md`.

16. **If tests were chosen**, wire Jest (already ships with `nest new`) for unit and/or
    Supertest for e2e per the answer; if "both" **and step 3 wasn't skipped** (i.e. Prisma was
    actually wired), also add Testcontainers (`@testcontainers/postgresql`) wired into the e2e
    Jest config to spin up a real Postgres per test run instead of mocking Prisma. A bot-only
    pure-client app has no Prisma to test against a real database — do not install
    Testcontainers for it regardless of the tests answer; instead, its e2e layer mocks/stubs the
    HTTP/WS surface of the backend it calls (e.g. `nock`/an in-memory fake server), documented
    the same way in `.agents/testing-and-quality.md`. Document the setup in the generated
    `.agents/testing-and-quality.md`.

17. **Generate the documentation tree** from `templates/`:
    - `CLAUDE.md`, `AGENTS.md` at project root.
    - `.agents/README.md` — flat index, kept in sync with whichever conditional files actually
      got generated.
    - `.agents/*.md` flat topic docs (workflow, git-policy, documentation, testing-and-quality,
      file-change-review, refactoring, progress — always include all of these) plus
      `agent-surface.md` only if
      mandatory TSDoc was chosen.
    - `.agents/code-style/` with its `README.md` hub + `imports.md`, `provider-structure.md`,
      `dto-and-validation.md`, `module-structure.md`.
    - `.agents/architecture/` with its `README.md` hub + `folder-structure.md`,
      `aliases-and-barrels.md`, `module-boundaries.md`, `transport-adapter.md`, and
      `messaging.md` only if messaging was chosen.
    - `.agents/shared/README.md` and `.agents/core/README.md` — both start with a registry
      table pre-populated with the always-on entries (Prisma, Logger, Health, the global
      Prisma exception filter), plus `core/health.md` and `core/logging.md` (always, not gated) and
      `core/auth.md` /
      `core/queue.md` / `core/cache.md` / `core/storage.md` / `core/i18n.md` only for the
      features actually chosen.
    - `.agents/decisions/README.md` — always generated, starts with no ADR files.
    - Fill every `{{PLACEHOLDER}}` with the real questionnaire answer. Leave no placeholder text.
    - Update `AGENTS.md`'s "Must Read" list to only reference files that were actually generated.

18. **`git init`, wire remote if given one, first commit.**
    - `git init` if not already a repo.
    - If the questionnaire gave a remote URL: `git remote add origin <url>`. If no URL was
      given, skip — do not invent or guess a remote.
    - Commit following the generated `.agents/git-policy.md` (commit message rules, no AI
      attribution).
    - Only push if the git-policy answer authorizes it without asking; otherwise stop after the
      commit and ask before pushing.

19. **Write the scaffold record**, `.agents/.kikita-scaffold.json` — the skill's own current
    commit (`git -C <skill-dir> rev-parse HEAD`, resolved from the running skill's own install
    location, not guessed) plus every questionnaire answer from step 1. `update.md` reads this
    on a later run to know what's already applied and how to resolve gates/placeholders
    without re-asking. This file must be committed, not gitignored — it's how a future update
    run identifies the project.

20. **Run `checklist.md`.** Fix anything that fails before reporting completion to the user.
