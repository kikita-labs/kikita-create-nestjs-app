# Adopt Plan

Runs when the skill is invoked inside an existing NestJS project that has no
`.agents/.kikita-scaffold.json` — a project this skill didn't scaffold. Generates the
`.agents/` documentation tree against what's actually there instead of assuming a blank
slate. Never runs `nest new`, never installs/replaces tooling the project already made its
own choice about (ORM, auth pattern, ESLint config, test runner, package manager) — this is a
docs retrofit, not a re-scaffold. If the project already has
`.agents/.kikita-scaffold.json`, this is the wrong file: use `update.md` instead.

## 1. Confirm scope before touching anything

This modifies a real, already-working project. Before writing a single file:

- Tell the user what you're about to do: generate `AGENTS.md` + `.agents/*` describing the
  project's actual current conventions, inferred from its config — not impose the skill's
  fixed defaults (Prisma+Postgres, the specific auth pattern, `nestjs-pino`, etc.) over an
  established codebase that may have made different, equally valid choices.
- Ask explicitly if this is wanted, and whether it's fine to also install the pieces this
  skill considers non-negotiable but the project is missing entirely (Husky pre-commit
  hooks) — offer these as opt-in additions, not silent installs, since a project that runs
  fine without them may have a reason.

## 2. Infer questionnaire answers from the existing project

Don't ask the full staged questionnaire from `SKILL.md` section 1 blind — read the project
first and only ask about what genuinely can't be determined by inspection:

- **Application type**: REST controllers under `src/**/*.controller.ts` → REST is in play.
  A bot platform dependency (`nestjs-telegraf`, `necord`, raw `discord.js`) plus
  `src/bot/updates/` (or similar) → bot is in play. Both present → "both".
- **Bot platform**: identify from the actual dependency in `package.json` — don't assume
  `necord` just because Discord is involved; check whether it's raw `discord.js` instead.
- **Bot owns its data**: `schema.prisma` / `@prisma/client` present → owns its data; if the
  bot makes no local DB calls and only hits an external backend's API, record that instead —
  don't force a database assumption onto a pure-client bot.
- **Tests**: `package.json` devDependencies for `jest`/`ts-jest`, `supertest`,
  `@testcontainers/postgresql`; a `test`/`test:e2e` script with no matching dependency is a
  signal the project's test setup is incomplete or was removed — flag it, don't guess.
- **Auth**: presence of a refresh-token/rotation flow, `argon2`/`argon2id` hashing,
  `csrf-csrf`, and a `RolesGuard` suggests this skill's fixed pattern; a *different* auth
  approach (sessions, bare JWT, a third-party auth provider) is a legitimate existing choice
  — describe what's actually there in `core/auth.md`, don't rewrite it to match the fixed
  default from a fresh scaffold.
- **Background jobs**: `bullmq` in dependencies.
- **Caching**: `@nestjs/cache-manager` + `@keyv/redis` in dependencies.
- **File uploads**: a storage adapter file (local disk and/or S3-compatible) plus Multer
  config in a controller/update handler.
- **Messaging**: `app.connectMicroservice()` call in `main.ts` plus a message-broker
  dependency (RabbitMQ client, or another broker the project chose instead — record which).
- **i18n**: `nestjs-i18n` in dependencies.
- **TSDoc policy**: sample a few exported symbols in `src/` — consistently documented means
  treat as "yes", otherwise "no". Judgment call; say so when reporting it.
- **Package manager**: whichever lockfile is present (`pnpm-lock.yaml` / `package-lock.json`
  / `yarn.lock`) — exactly one should exist; flag it if more than one does instead of
  picking.
- **Folder layout**: inventory `src/` by ownership, not only by filename suffix. Treat a
  business/domain feature under `src/core/` as a structural finding, not as a core singleton.
  Treat `@Global()` on a domain module as a visibility choice, not proof that the module belongs
  in `core/`.
  Treat a feature root with more than six production `.ts` files, or with several unrelated
  capability groups, as an over-flat feature. Adoption is documentation-only: describe the
  current layout accurately, call out the deviation and recommended target in the architecture
  docs (including a deviation row in `core/README.md` if a domain module is still under `core/`),
  and do not move existing source files unless the user separately asks for a refactor. Do not
  use an existing over-flat feature as the template for new files; use the preferred
  responsibility-first layout for new work and record the legacy deviation.
- **Git policy**: ask — this isn't inferrable from the repo.

For the fixed defaults this skill normally never asks about (ORM/DB, validation shape,
response serialization, Swagger, CORS, API versioning, rate limiting, logging, health
checks, graceful shutdown, Prisma error mapping) — don't assume the project matches them.
Check what's actually there (e.g. TypeORM instead of Prisma, no `/health/ready` route at
all) and describe the real setup in the generated docs. Flag any genuinely missing
non-negotiable (no rate limiting, no CORS allowlist) as a finding for the user, not
something to silently add.

Report the inferred answers back to the user before generating anything, so they can
correct a wrong guess (e.g. a queue library detected but not actually wired into any
module).

## 3. Generate the documentation tree

Follow `SKILL.md` section 2 / `plan.md`'s file list and placeholder-filling rules, using the
answers from step 2 instead of a fresh questionnaire. Differences from a fresh scaffold:

- Do not touch `package.json` scripts, `prisma/schema.prisma`, ESLint config, or any
  existing tooling file — describe what's actually configured in the generated docs, don't
  change it to match the template's defaults. If something the docs assume is missing
  entirely (e.g. no Prettier config at all), note it in the relevant doc rather than
  silently installing it, unless the user opted in during step 1.
- `.agents/code-style/*.md`, `.agents/architecture/*.md`, `.agents/core/*.md` etc. must
  describe the project's real folder structure and patterns as they exist today, not the
  template's example layout — read `src/` first (`common/`, `core/`, `modules/`, `bot/`, or
  whatever's actually there) and adapt the doc content, don't paste the template verbatim.
- `.agents/core/logging.md` is always generated during adoption. It must describe the logger,
  exception boundaries, correlation, redaction, and known gaps that actually exist; adoption must
  not silently upgrade the code or present optional telemetry as already configured.
- Skip `git init` — the project already has its history; just make sure the new `.agents/`
  files get committed in a normal commit once the user reviews them.

## 4. Write the scaffold record

Same shape as a fresh scaffold's `.agents/.kikita-scaffold.json` (`plan.md`'s generation
step), plus a marker that this was adopted, not scaffolded, and when:

```json
{
  "skill": "kikita-create-nestjs-app",
  "scaffoldedFromCommit": "<skill repo HEAD at adoption time>",
  "adopted": true,
  "adoptedAt": "{{DATE}}",
  "answers": { "...": "as inferred/confirmed in step 2" }
}
```

`scaffoldedFromCommit` being the *adoption*-time commit (not a real historical scaffold
point) is expected and correct — `update.md` only needs a starting point to diff forward
from, it doesn't need real history predating adoption.

## 5. Verify and hand back

Run the "Documentation" section of `checklist.md` (not "Setup"/"Data layer"/"Validation,
logging, transport"/"Optional features"/"Tooling" — those assume a fresh scaffold's exact
toolchain, which adoption deliberately doesn't touch). Report what was generated, what was
inferred vs. confirmed by the user, and anything flagged as incomplete or deviating from
this skill's fixed defaults in step 2 (missing test runner, a different ORM, no rate
limiting) so the user can follow up.
