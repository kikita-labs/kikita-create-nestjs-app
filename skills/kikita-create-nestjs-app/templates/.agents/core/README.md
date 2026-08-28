# Core

Registry of `src/core/` singletons: app-wide providers that exist exactly once for the whole
app and usually wrap external state/connections (a DB client, a broker connection, a cache
client). Not a dumping ground for "things that didn't fit elsewhere" — see
`../architecture/folder-structure.md` for the boundary between `core/` and `common/`.

`core/<name>/` is a single infrastructure boundary, not a domain-feature folder. A provider
that coordinates legal rules, user actions, reports, or another business capability belongs
under `src/modules/<feature>/`, even if it is used by more than one transport or has one singleton
instance. `@Global()` only changes DI visibility; it is not evidence that a provider belongs in
`core/`. Use a global module for shared infrastructure sparingly and prefer explicit imports for
domain modules. If a legacy domain module remains here temporarily, mark the registry row as a
documented deviation and record `src/modules/<feature>/` as its migration target; do not present
the placement as the preferred architecture.

## Registry

| Name | Kind | Path | Doc | Summary |
| --- | --- | --- | --- | --- |
<!-- SCAFFOLD: keep only if this project has Prisma — skipped for a bot-only app that's a pure client to an existing backend, see plan.md step 3's gate -->
| PrismaService | service | `core/prisma/` | — | Wraps `PrismaClient`, hooks `OnModuleInit`/`OnModuleDestroy` for connection lifecycle. Global. Lifecycle hooks only fire because `main.ts` calls `app.enableShutdownHooks()` — see `../architecture/transport-adapter.md`. |
| Logger | service | `core/logger/` | [logging.md](./logging.md) | `nestjs-pino` structured JSON logger, wired as the app's bootstrap logger. Global. Read the logging and error-observability policy before adding catches, filters, or log events. |
| Health | module | `core/health/` | [health.md](./health.md) | `@nestjs/terminus`, two routes: `/health/live` (process-only) and `/health/ready` (Prisma + Redis/RabbitMQ if chosen — or the upstream backend's own health endpoint via `HttpHealthIndicator`, for a bot-only app with no Prisma). Always present, not questionnaire-gated. |
<!-- SCAFFOLD: keep only if auth was chosen -->
| Auth | module | `core/auth/` | [auth.md](./auth.md) | Access/refresh JWT, `RolesGuard`, `argon2id` hashing. |
<!-- SCAFFOLD: keep only if background jobs was chosen -->
| Queue | module | `core/queue/` | [queue.md](./queue.md) | BullMQ wiring against Redis. |
<!-- SCAFFOLD: keep only if caching was chosen -->
| Cache | module | `core/cache/` | [cache.md](./cache.md) | `@nestjs/cache-manager` + `@keyv/redis`, cache-aside. |
<!-- SCAFFOLD: keep only if file uploads was chosen -->
| Storage | module | `core/storage/` | [storage.md](./storage.md) | S3-compatible storage adapter (local dev / real bucket prod). |
<!-- SCAFFOLD: keep only if i18n was chosen -->
| I18n | module | `core/i18n/` | [i18n.md](./i18n.md) | `nestjs-i18n`, locale resolution (REST + bot), validation message translation. |

Kind is one of: `service`, `module`, `guard`, `interceptor`, `token`.

A custom-provider injection token (`provide: SOME_TOKEN`, injected via `@Inject(SOME_TOKEN)`)
that belongs to one of the modules already in this table — `STORAGE_ADAPTER` inside
`core/storage/`, for example — is that module's implementation detail, not its own registry
row. A token with no owning module (app-wide, used by more than one unrelated consumer, or
not tied to a single feature) is `kind: token`, path `core/tokens/<name>.token.ts`, and does
get its own row — don't leave it flat directly under `core/` uncategorized.

## Adding an entry

1. Build it under `src/core/<name>/` (see `../architecture/folder-structure.md`), or
   `src/core/tokens/` for a standalone token with no owning module.
2. Add a row to the table above.
3. If it has non-trivial wiring or a public API other modules depend on, create
   `.agents/core/<name>.md`. A simple wrapper service can rely on the table row alone.
4. If it wraps a real connection (DB, broker, cache), it's almost always meant to be
   `@Global()` (or re-exported from `AppModule` for every feature module to use without an
   explicit import) — see `../architecture/module-boundaries.md`.

This applies every time a core singleton is added, changed, or removed — see
`../documentation.md`.

## Review Checklist

- [ ] Table has no stale or missing entries.
- [ ] Nothing here that's actually feature-scoped — that belongs in `../shared/README.md` or a
      `modules/*` folder instead.
- [ ] Every entry wrapping a real connection is `@Global()` or re-exported from `AppModule`.
- [ ] Logger changes follow `logging.md`: structured fields, redaction, correlation, and one
      final error-logging boundary are verified.
