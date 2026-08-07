# Folder Structure

Feature-based, not layer-based: a module owns everything it needs (controller/update-handler,
service, DTOs, guards, its own spec files) in one folder. Never split by technical layer at the
top level (no `src/controllers/`, `src/services/`, `src/dtos/` siblings). Every file type used
in this project has exactly one correct home — this section is the exhaustive map, not a partial
example. If a new file doesn't obviously fit a row below, that's a signal to stop and ask, not to
invent a new top-level folder.

```
src/
  main.ts                      <- bootstrap only, see architecture/transport-adapter.md
  app.module.ts                 <- root module, imports every feature module + core/common
  common/                       <- reusable, NO app-wide state — could be copy-pasted into
                                    another Nest project and still work standalone
    pipes/          *.pipe.ts
    filters/         *.filter.ts
      prisma-exception.filter.ts  <- always present, global APP_FILTER
    interceptors/    *.interceptor.ts
    guards/          *.guard.ts        <- cross-feature guards only (ThrottlerGuard subclass,
                                           RolesGuard); a guard used by exactly one feature
                                           lives in that feature's own guards/ instead
    middleware/      *.middleware.ts   <- e.g. request-id middleware; NOT global pipes/filters,
                                           those are their own folders above
    decorators/      *.decorator.ts    <- custom param/method decorators (@CurrentUser())
    exceptions/      *.exception.ts    <- custom classes extending HttpException; NOT filters
                                           (a filter catches/maps, an exception is thrown)
    interfaces/      *.interface.ts    <- cross-feature shared interfaces/types only
    enums/           *.enum.ts         <- cross-feature shared enums only
    constants/       *.constant.ts     <- cross-feature shared constants only
    utilities/       *.util.ts         <- zero @nestjs/* imports, plain functions/classes,
                                           enforced by ESLint (architecture/README.md)
  core/                          <- app-wide singletons, exactly one instance for the whole app,
                                    registered in core/README.md
    config/
      env.schema.ts              <- Zod schema + validate(), the one file allowed to read
                                     process.env directly (code-style/dto-and-validation.md)
    prisma/
      prisma.service.ts
      prisma.module.ts
    logger/            logger.module.ts   <- wraps nestjs-pino's LoggerModule.forRootAsync()
    health/                       <- always present, see core/health.md
      health.controller.ts
      health.module.ts
      indicators/                 <- one *.health-indicator.ts per external dependency actually
                                      wired (Prisma always; Redis/RabbitMQ if chosen)
    <!-- SCAFFOLD: keep only if auth was chosen -->
    auth/
      auth.controller.ts
      auth.service.ts
      auth.module.ts
      guards/         jwt-auth.guard.ts, roles.guard.ts
      strategies/     jwt.strategy.ts    <- Passport strategies
      decorators/     roles.decorator.ts, current-user.decorator.ts
      dto/            login.dto.ts, refresh.dto.ts
    <!-- SCAFFOLD: keep only if background jobs was chosen -->
    queue/            queue.module.ts     <- shared BullMQ connection wiring only; individual
                                              queues/processors live in the owning feature module
    <!-- SCAFFOLD: keep only if caching was chosen -->
    cache/            cache.module.ts
    <!-- SCAFFOLD: keep only if file uploads was chosen -->
    storage/
      storage.interface.ts
      local-storage.adapter.ts
      s3-storage.adapter.ts
      storage.module.ts
    <!-- SCAFFOLD: keep only if i18n was chosen -->
    i18n/              i18n.module.ts   <- nestjs-i18n wiring, see core/i18n.md
    tokens/            <- standalone injection tokens with no owning module (app-wide,
                            used by more than one unrelated consumer); a token that
                            belongs to one module above (e.g. STORAGE_ADAPTER inside
                            storage/) stays there instead — created on demand, not
                            scaffolded empty
  <!-- SCAFFOLD: keep only if i18n was chosen -->
  i18n/                          <- translation content, not code
    en/                *.json           <- one file per namespace (errors.json, users.json, ...),
                                            fallback locale, every key must exist here
    <!-- other locale folders as they're added -->
  modules/                       <- business features, one folder per feature
    users/
      users.module.ts
      users.controller.ts         <!-- SCAFFOLD: keep only if REST or both -->
      users.service.ts
      dto/              create-user.dto.ts, update-user.dto.ts, user-response.dto.ts
      interfaces/                 <- only if this feature has 2+ reusable interfaces; a single
                                     one-off type stays inline in the file that uses it
      constants/                  <- only if this feature has a reusable constant/lookup table
      guards/                     <- only if this feature has a guard nothing else needs
      reports/                    <- sub-resource subfolder: a route prefix that split off the
                                     base controller AND grew its own dto/ (see
                                     code-style/module-structure.md's "Multiple controllers per
                                     module") — a sub-resource that's still a single file with
                                     no DTOs of its own can stay a flat sibling file instead
        user-reports.controller.ts
        user-reports.service.ts   <- only if the sub-resource's logic is non-trivial, same doc
        dto/
          user-report-response.dto.ts
      users.service.spec.ts
  <!-- SCAFFOLD: keep only if bot or both was chosen -->
  bot/
    bot.module.ts
    updates/          *.update.ts    <- generic event-handler layer, see transport-adapter.md
    scenes/           *.scene.ts     <- multi-step conversation flows, if the platform has them
prisma/
  schema.prisma
  migrations/
test/                             <!-- SCAFFOLD: keep only if e2e tests were chosen -->
```

## File-type → folder, quick lookup

| File type | Suffix | Feature-specific home | Cross-feature home |
| --- | --- | --- | --- |
| Controller | `.controller.ts` | `modules/<feature>/` | — (controllers are never cross-feature) |
| Service | `.service.ts` | `modules/<feature>/` | `core/<name>/` if it's a true app-wide singleton |
| Module | `.module.ts` | `modules/<feature>/` | `core/<name>/` |
| DTO | `.dto.ts` | `modules/<feature>/dto/` | — |
| Bot update handler | `.update.ts` | `bot/updates/` | — |
| Bot scene | `.scene.ts` | `bot/scenes/` | — |
| Queue processor | `.processor.ts` | `modules/<feature>/` (owning feature) | — |
| Passport strategy | `.strategy.ts` | — | `core/auth/strategies/` |
| Pipe | `.pipe.ts` | `modules/<feature>/` if feature-only | `common/pipes/` |
| Filter | `.filter.ts` | `modules/<feature>/` if feature-only | `common/filters/` |
| Interceptor | `.interceptor.ts` | `modules/<feature>/` if feature-only | `common/interceptors/` |
| Guard | `.guard.ts` | `modules/<feature>/guards/` | `common/guards/` or `core/auth/guards/` |
| Middleware | `.middleware.ts` | — (middleware is applied app-wide or per-module in `configure()`) | `common/middleware/` |
| Param/method decorator | `.decorator.ts` | `modules/<feature>/` if feature-only | `common/decorators/` |
| Custom exception | `.exception.ts` | `modules/<feature>/` if feature-only | `common/exceptions/` |
| Interface/type | `.interface.ts` | `modules/<feature>/interfaces/` (2+ reusable) or inline (1-off) | `common/interfaces/` |
| Enum | `.enum.ts` | `modules/<feature>/enums/` | `common/enums/` |
| Constant | `.constant.ts` | `modules/<feature>/constants/` | `common/constants/` |
| Utility function | `.util.ts` | `modules/<feature>/` if feature-only | `common/utilities/` (zero `@nestjs/*` imports) |
| Test | `.spec.ts` | next to the file under test | next to the file under test |
| Storage adapter | `.adapter.ts` | — | `core/storage/` |
| Health indicator | `.health-indicator.ts` | — | `core/health/indicators/` |

A file moves from a feature's own subfolder to the matching `common/` folder the moment a
**second** feature needs it — not preemptively. Don't create an empty `interfaces/`/`enums/`/
`constants/`/`guards/` subfolder in a feature that has nothing to put in it yet — create the
subfolder in the same commit as the first file that actually belongs there.

## No inline reusable declarations

An `interface`/`type`/`enum`/exported `const` meant to be reused across more than the one file
that declares it never stays inline in a `.controller.ts`/`.service.ts`/`.dto.ts` — it goes in
the matching `interfaces/`/`enums`/`constants/` subfolder from the table above, even if that
means creating the subfolder for the first time in that feature. A one-off type used by exactly
one function in exactly one file is the only case allowed to stay inline.

## `common/` vs `core/` vs `modules/`

- `common/` — reusable pieces with **no app-wide state**: a validation pipe, an exception
  filter, a decorator, a plain utility function. Anything here could be copy-pasted into a
  different Nest project and still work standalone.
- `core/` — singletons that exist **exactly once for the whole app** and usually hold or wrap
  state/connections: the Prisma client, the auth module, the queue/cache/storage wiring, the
  logger, health checks. Registered in `.agents/core/README.md`.
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
- [ ] Every file placed per the file-type table above — no ad hoc top-level folder invented for
      a file type already covered by the table.
- [ ] No reusable `interface`/`enum`/exported `const` left inline — moved to the matching
      subfolder the moment a second file needs it.
- [ ] Nothing under `common/utilities/` imports `@nestjs/*`.
- [ ] Nothing under `core/` imports from `modules/*`.
- [ ] No empty `interfaces/`/`enums/`/`constants/`/`guards/` subfolder committed with nothing in
      it — created only when the first file that belongs there exists.
- [ ] No `index.ts` barrel file anywhere — see `aliases-and-barrels.md` for why.
