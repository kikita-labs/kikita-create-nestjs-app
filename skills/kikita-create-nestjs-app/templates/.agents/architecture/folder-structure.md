# Folder Structure

Feature-based, not layer-based: a small module owns everything it needs (controller/update-handler,
service, DTOs, guards, and its own spec files) in one dedicated feature folder. This does not
mean that a large feature becomes one flat directory. Keep the feature root for its composition
files and split distinct capabilities into named child folders as the feature grows. Never split
the application into technical layer folders at the top level (no `src/controllers/`,
`src/services/`, or `src/dtos/` siblings). Every file type used in this project has exactly one
correct home — this section is the exhaustive map, not a partial example. If a new file doesn't
obviously fit a row below, that's a signal to stop and ask, not to invent a new top-level folder.

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
      interactions/                <- a named capability, not a generic services/ bucket
        user-interactions.controller.ts
        user-interactions.service.ts
        dto/
          create-user-interaction.dto.ts
        clients/
          user-status.client.ts
        builders/
          user-modal.builder.ts
        state/
          pending-user-action.store.ts
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

## Feature roots and capability folders

Nest's official feature-module example keeps a small feature's module, controller, and service
together, with `dto/` and `interfaces/` below it. Follow that shape while the feature is small.
Use these rules when it grows:

- Classify before choosing a path. First identify the business capability, then the file's role
  (controller, provider, client, builder, store, guard, or type), then its visibility and
  consumers. The filename suffix describes the role; it does not decide the folder by itself.
- A folder list is not a design. Do not create a file merely to fill `constants/`, `interfaces/`,
  or another familiar folder. Start with the dependency/consumer graph and choose the smallest
  cohesive vertical slice that owns the behavior.
- Keep `modules/<feature>/` for the feature module, its primary controller/service, and files
  shared by the whole feature.
- Treat **six production `.ts` files at the feature root** as the maximum. Count `.module.ts`,
  controllers, providers, clients, builders, stores, and other runtime files; do not count
  nested files or `.spec.ts` files. Split earlier when the root already contains two distinct
  capabilities. This is a review threshold, not a NestJS framework limit.
- Name a child folder after the business capability or sub-resource (`reports/`, `interactions/`,
  `billing/`, `webhooks/`), then keep that capability vertically cohesive: its controller,
  providers, DTOs, adapters, clients, builders, state, and tests stay together.
- A capability folder may use the recognized subfolders in the table below, but role folders are
  optional. Keep one client, builder, store, or registry beside the related flow when that is the
  clearest ownership; create `clients/`, `builders/`, or `state/` only when there are multiple
  related files or a real subsystem boundary. Never create generic technical buckets such as
  `services/`, `controllers/`, `dtos/`, `utils/`, `types/`, or `misc/`.
- Treat `constants/` the same way: keep one file per cohesive constant family, not one file per
  constant and not one giant `<feature>.constants.ts` grab bag. Split independent action, error,
  metrics, modal, or lifecycle families into separate files when their consumers differ.
- Register capability providers in the owning feature module. Add a nested `*.module.ts` only
  when that capability has a real Nest module boundary; a folder alone is an organizational
  boundary, not a second deployable service.
- Apply the same rule to `core/<name>/`: it is for one app-wide infrastructure singleton or
  wrapper, not a place to hide a domain feature. For example, legal business logic belongs under
  `src/modules/legal/`, not `src/core/legal/`; a legal status client belongs in the relevant
  `modules/legal/<capability>/` folder unless it is truly shared by the whole application.

Do not flatten a feature merely because every class shares the same filename prefix. A folder
containing a registry, metrics provider, external client, modal builder, interaction guard, and
pending-action store already has several responsibilities and must be split by capability. Group
files that participate in one workflow together even when their suffixes differ; a modal builder,
modal update handler, interaction guard, status client, and pending-action store may all belong in
one `acceptance/` capability, with only the guard in `acceptance/guards/` if that makes its Nest
role clearer.

For a legal acceptance flow like the one shown in this project's examples, a reasonable target is:

```
modules/legal/
  legal.module.ts
  legal.module.spec.ts
  constants/                    <- one cohesive file per constant family, not one file per value
    legal-action.constants.ts
    legal-error-code.constants.ts
    legal-metrics.constants.ts
    legal-modal.constants.ts
    legal-pending-action.constants.ts
    legal-status.constants.ts
  actions/
    legal-action.decorator.ts
    legal-action-registry.service.ts
    interfaces/
      legal-action-adapter.interface.ts
  acceptance/
    legal-modal.builder.ts
    legal-modal.update.ts
    legal-status.client.ts
    pending-legal-action.store.ts
    interfaces/
      pending-legal-action.interface.ts
    guards/
      legal-interaction.guard.ts
  errors/
    legal-error-code.util.ts
  metrics/
    legal-metrics.service.ts
    interfaces/
      legal-metric-snapshot.interface.ts
```

Keep `legal-metric-snapshot.interface.ts` inline in `legal-metrics.service.ts` if it has only one
consumer and is not part of the capability's public API. Keep private maps and private helper
types inside `legal-error-code.util.ts` when no other file consumes them. Move a declaration out
when another file imports it, or when it represents a public contract rather than an implementation
detail.

## File-type → folder, quick lookup

| File type | Suffix | Feature-specific home | Cross-feature home |
| --- | --- | --- | --- |
| Controller | `.controller.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` | — (controllers are never cross-feature) |
| Service | `.service.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` | `core/<name>/` if it's a true app-wide singleton |
| Module | `.module.ts` | `modules/<feature>/` or a real nested capability module | `core/<name>/` |
| DTO | `.dto.ts` | `modules/<feature>/dto/` or `modules/<feature>/<capability>/dto/` | — |
| Bot update handler | `.update.ts` | `bot/updates/` | — |
| Bot scene | `.scene.ts` | `bot/scenes/` | — |
| Queue processor | `.processor.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` (owning feature) | — |
| Passport strategy | `.strategy.ts` | — | `core/auth/strategies/` |
| Pipe | `.pipe.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/pipes/` |
| Filter | `.filter.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/filters/` |
| Interceptor | `.interceptor.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/interceptors/` |
| Guard | `.guard.ts` | `modules/<feature>/guards/` or `modules/<feature>/<capability>/guards/` | `common/guards/` or `core/auth/guards/` |
| Middleware | `.middleware.ts` | — (middleware is applied app-wide or per-module in `configure()`) | `common/middleware/` |
| Param/method decorator | `.decorator.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/decorators/` |
| Custom exception | `.exception.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/exceptions/` |
| Interface/type | `.interface.ts` | `modules/<feature>/interfaces/` or `modules/<feature>/<capability>/interfaces/` (2+ reusable) or inline (1-off) | `common/interfaces/` |
| Enum | `.enum.ts` | `modules/<feature>/enums/` or `modules/<feature>/<capability>/enums/` | `common/enums/` |
| Constant | `.constant.ts` | `modules/<feature>/constants/` or `modules/<feature>/<capability>/constants/` | `common/constants/` |
| Utility function | `.util.ts` | `modules/<feature>/` or `modules/<feature>/<capability>/` if feature-only | `common/utilities/` (zero `@nestjs/*` imports) |
| Test | `.spec.ts` | next to the file under test | next to the file under test |
| Adapter | `.adapter.ts` | `modules/<feature>/<capability>/` or `.../adapters/` when multiple | `core/<name>/` if app-wide; `core/storage/` for the storage feature |
| External client | `.client.ts` | `modules/<feature>/<capability>/` or `.../clients/` when multiple | `core/<name>/` only if app-wide |
| Builder/factory | `.builder.ts` / `.factory.ts` | `modules/<feature>/<capability>/` or `.../builders/` when multiple | `common/utilities/` only when framework-agnostic |
| State store | `.store.ts` | `modules/<feature>/<capability>/` or `.../state/` when multiple | `core/<name>/` only if app-wide |
| Registry | `.registry.ts` | `modules/<feature>/<capability>/` | `core/<name>/` only if app-wide |
| Health indicator | `.health-indicator.ts` | — | `core/health/indicators/` |

A file moves from a feature's own subfolder to the matching `common/` folder the moment a
**second** feature needs it — not preemptively. Don't create an empty `interfaces/`/`enums/`/
`constants/`/`guards/` subfolder in a feature that has nothing to put in it yet — create the
subfolder in the same commit as the first file that actually belongs there. If two capabilities in
the same feature need a declaration, promote it to the feature-level matching folder before
promoting it to `common/`.

## No inline reusable declarations

An `interface`/`type`/`enum`/exported `const` meant to be reused across more than the one file
that declares it never stays inline in a `.controller.ts`/`.service.ts`/`.dto.ts` — it goes in
the matching `interfaces/`/`enums/`/`constants/` subfolder from the table above, even if that
means creating the subfolder for the first time in that feature. A one-off type used by exactly
one function in exactly one file is the only case allowed to stay inline. A private map or helper
type used only by one utility file may also stay there; do not extract implementation details just
to populate a folder. An exported declaration is not automatically shared — check its imports.

`*.util.ts` files contain pure, feature-specific helper functions and their private implementation
details. They do not become a generic `utilities/` bucket, and they must not contain Nest
providers, services, or unrelated feature constants. Put an error-normalization helper under the
feature's `errors/` capability, for example, not under `legal/utilities/`; move a genuinely
cross-feature, framework-agnostic helper to `common/utilities/`.

## `common/` vs `core/` vs `modules/`

- `common/` — reusable pieces with **no app-wide state**: a validation pipe, an exception
  filter, a decorator, a plain utility function. Anything here could be copy-pasted into a
  different Nest project and still work standalone.
- `core/` — technical singletons that exist **exactly once for the whole app** and usually hold
  or wrap state/connections: the Prisma client, the auth module, the queue/cache/storage wiring,
  the logger, health checks. Registered in `.agents/core/README.md`. Classify by ownership, not
  by instance count: a domain module can also be a singleton and still belongs in `modules/`.
- `modules/` — business features. Each imports from `common/` and `core/`, never the other way
  around (a `core/` provider must not depend on a `modules/*` service — that's an inverted
  dependency and a sign the logic belongs in `modules/` instead).

`@Global()` changes DI visibility; it does not change ownership. Do not use `@Global()` as a
reason to move a business feature into `core/` or to make every provider available everywhere.
Nest's own guidance recommends using explicit `imports` for controlled module APIs and reserving
global modules for shared infrastructure. A cross-cutting domain feature such as legal acceptance
stays under `modules/legal/`; if it truly needs global visibility, document that exception in an
ADR and keep its domain ownership visible.

## `bot/` vs `modules/`

The bot's `updates/` folder is a thin transport layer, structurally equivalent to REST
controllers — it translates an incoming platform event into a call on a `modules/*` service and
formats the reply. Business logic (validation beyond input shape, persistence, side effects)
lives in `modules/`, never inline in an update handler, so the same logic is reachable from both
REST and bot transports when both are chosen. See `transport-adapter.md`.

## Review Checklist

- [ ] No top-level `controllers/`/`services/`/`dtos/` layer folders — everything grouped by
      feature under `modules/`.
- [ ] No business/domain feature lives under `core/`; every `core/<name>/` entry is a registered
      app-wide singleton or infrastructure wrapper.
- [ ] No feature root exceeds six production `.ts` files or mixes distinct capabilities without
      named child folders; no generic `services/`/`utils/`/`misc/` bucket hides the split.
- [ ] Every file placed per the file-type table above — no ad hoc top-level folder invented for
      a file type already covered by the table.
- [ ] No reusable `interface`/`enum`/exported `const` left inline — moved to the matching
      subfolder the moment a second file needs it.
- [ ] Paths were chosen from a responsibility/consumer inventory, not from the list of already
      existing folders or from a filename prefix.
- [ ] A large constants file was split by cohesive constant family; private one-file maps/types
      were not extracted without a reuse or public-contract reason.
- [ ] Nothing under `common/utilities/` imports `@nestjs/*`.
- [ ] Nothing under `core/` imports from `modules/*`.
- [ ] No empty `interfaces/`/`enums/`/`constants/`/`guards/` subfolder committed with nothing in
      it — created only when the first file that belongs there exists.
- [ ] No `index.ts` barrel file anywhere — see `aliases-and-barrels.md` for why.
