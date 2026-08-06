# Folder Structure

Feature-based, not layer-based: a module owns everything it needs (controller/update-handler,
service, DTOs, its own spec files) in one folder. Never split by technical layer at the top
level (no `src/controllers/`, `src/services/`, `src/dtos/` siblings).

```
src/
  main.ts                    <- bootstrap, global pipes/filters, versioning, CORS, Swagger
  app.module.ts               <- root module, imports every feature module + core/common
  common/                     <- framework-agnostic + generic cross-cutting pieces
    pipes/
    filters/
      prisma-exception.filter.ts <- always present, global APP_FILTER, see transport-adapter.md
    interceptors/
    decorators/
    utilities/                 <- zero @nestjs/* imports, plain functions/classes
  core/                        <- app-wide singletons, registered in core/README.md
    prisma/
      prisma.service.ts
      prisma.module.ts
    logger/
    health/                     <- always present, GET /health via @nestjs/terminus
    <!-- SCAFFOLD: keep only if auth was chosen -->
    auth/
    <!-- SCAFFOLD: keep only if background jobs was chosen -->
    queue/
    <!-- SCAFFOLD: keep only if caching was chosen -->
    cache/
    <!-- SCAFFOLD: keep only if file uploads was chosen -->
    storage/
  modules/                     <- business features, one folder per feature
    users/
      users.module.ts
      users.controller.ts       <!-- SCAFFOLD: keep only if REST or both -->
      users.service.ts
      dto/
        create-user.dto.ts
        update-user.dto.ts
      users.service.spec.ts
  <!-- SCAFFOLD: keep only if bot or both was chosen -->
  bot/
    bot.module.ts
    updates/                    <- generic event-handler layer, see transport-adapter.md
      start.update.ts
    scenes/                     <- multi-step conversation flows, if the platform supports them
prisma/
  schema.prisma
  migrations/
test/                           <!-- SCAFFOLD: keep only if e2e tests were chosen -->
```

## `common/` vs `core/` vs `modules/`

- `common/` — reusable pieces with **no app-wide state**: a validation pipe, an exception
  filter, a decorator, a plain utility function. Anything here could be copy-pasted into a
  different Nest project and still work standalone.
- `core/` — singletons that exist **exactly once for the whole app** and usually hold or wrap
  state/connections: the Prisma client, the auth module, the queue/cache/storage wiring, the
  logger. Registered in `.agents/core/README.md`.
- `modules/` — business features. Each imports from `common/` and `core/`, never the other way
  around (a `core/` provider must not depend on a `modules/*` service — that's an inverted
  dependency and a sign the logic belongs in `modules/` instead).

## `bot/` vs `modules/`

The bot's `updates/` folder is a thin transport layer, structurally equivalent to REST
controllers — it translates an incoming platform event into a call on a `modules/*` service and
formats the reply. Business logic (validation beyond input shape, persistence, side effects)
lives in `modules/`, never inline in an update handler, so the same logic is reachable from both
REST and bot transports when both are chosen. See `transport-adapter.md`.

## Review Checklist

- [ ] No top-level `controllers/`/`services/`/`dtos/` layer folders — everything grouped by
      feature under `modules/`.
- [ ] Nothing under `common/utilities/` imports `@nestjs/*`.
- [ ] Nothing under `core/` imports from `modules/*`.
- [ ] Every module folder has a barrel `index.ts` if it holds more than its own module/
      controller/service files (see `aliases-and-barrels.md`).
