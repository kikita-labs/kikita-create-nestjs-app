# Module Structure

Every `*.module.ts` follows the same field order in its `@Module()` decorator — makes modules
scannable and diffs small when only one section changes:

```ts
@Module({
  imports: [PrismaModule, OtherFeatureModule],
  controllers: [UsersController, UserReportsController], // omit entirely for a bot-only/broker-only module
  providers: [UsersService, UserReportsService],
  exports: [UsersService],
})
export class UsersModule {}
```

1. `imports` — other modules this one depends on, `core/` modules first, then other `modules/*`.
2. `controllers` — REST controllers, if this module has any. One per route-prefix/sub-resource,
   not one giant controller for the whole feature — see "Multiple controllers per module" below.
   Omit the key if none (don't write `controllers: []`).
3. `providers` — services, guards, interceptors, and anything else DI-managed that's specific to
   this module. A bot's `updates/*.update.ts` classes are registered here too (Telegraf/Necord
   update classes are just injectables).
4. `exports` — the module's public surface, see `../architecture/module-boundaries.md`. Only
   list what another module is actually meant to consume.

## Multiple controllers per module (sub-resources)

A feature's REST surface is not required to live in one `<feature>.controller.ts` — `controllers`
takes an array, and Nest has no problem with more than one entry. Split into a separate
controller the moment a feature grows a sub-resource with its own route prefix — don't grow one
controller class into a dumping ground for every route that happens to touch the same Prisma
model.

**Flat sibling file vs its own subfolder** — don't default to flat: a sub-resource that's
genuinely one file (a controller with no DTOs of its own, reusing the parent's) can sit as a
sibling file next to `<feature>.controller.ts`; the moment it grows its **own `dto/`** (a
response shape, a query DTO — which happens almost immediately, since a sub-resource meaningful
enough to get its own controller is usually meaningful enough to get its own response shape
too), promote it to its own subfolder under the feature, `modules/<feature>/<sub-resource>/`,
mirroring the same internal layout a top-level feature gets. This keeps `modules/<feature>/`'s
root from accumulating a flat pile of `<sub-resource>.controller.ts` /
`<sub-resource>.service.ts` / `<sub-resource>-response.dto.ts` files as more sub-resources
appear — each sub-resource gets exactly one place to live, not three files scattered loose at
the parent level.

Concretely, for a `users` feature that grows a `/v1/users/reports/unresolved`-style surface:

```
modules/users/
  users.module.ts
  users.controller.ts       <- /v1/users, /v1/users/:id (base CRUD)
  users.service.ts
  dto/
    create-user.dto.ts
    update-user.dto.ts
  reports/                   <- sub-resource subfolder, created once it has its own dto/
    user-reports.controller.ts   <- /v1/users/reports/...
    user-reports.service.ts      <- only if the sub-resource's logic is non-trivial, see below
    dto/
      user-report-response.dto.ts
```

Route paths stay plain string literals directly in the decorator — `@Controller('users')`,
`@Controller('users/reports')` — matching idiomatic Nest (every official example does this; the
framework's own routing/param-matching tooling, including
`@darraghor/eslint-plugin-nestjs-typed`'s `param-decorator-name-matches-route-param` rule,
assumes a literal string and breaks on anything else). Don't reach for an enum or a shared
constants object here the way `architecture/routing.md`-style Angular conventions might suggest
— that's a different framework with a structurally different routing mechanism (runtime route
config objects, not decorator arguments evaluated at class-definition time), and porting the
convention over gains nothing here while breaking real tooling.

The sub-resource's controller/service/module registration stay exactly as before — only the
file location changes, imported via a slightly longer relative path
(`./reports/user-reports.controller.ts` from `users.module.ts`):

```ts
// modules/users/reports/user-reports.controller.ts
@Controller({ path: 'users/reports', version: '1' })
export class UserReportsController {
  constructor(private readonly userReportsService: UserReportsService) {}

  @Get('unresolved')
  findUnresolved(): Promise<UserReportResponseDto[]> {
    return this.userReportsService.findUnresolved();
  }
}
```

```ts
// modules/users/users.module.ts
import { UserReportsController } from './reports/user-reports.controller';
import { UserReportsService } from './reports/user-reports.service';

@Module({
  controllers: [UsersController, UserReportsController],
  providers: [UsersService, UserReportsService],
  exports: [UsersService],
})
export class UsersModule {}
```

**When to give the sub-resource its own service file vs reusing the existing one**: if the
sub-resource's logic is a couple of pass-through calls into queries the main service already
has, it's fine for `UserReportsController` to inject `UsersService` directly — don't create a
service file with nothing real in it. The moment the sub-resource has its own non-trivial
queries, validation, or side effects, give it its own `<sub-resource>.service.ts` so
`UsersService` doesn't grow unrelated methods that have nothing to do with a "user" as such.

**When to promote the sub-resource to its own top-level module instead of a subfolder in
`users/`**: only when it stops being genuinely user-scoped — e.g. a `reports` concern that spans
multiple unrelated features, not just users, belongs in its own `modules/reports/` from the
start. A sub-resource whose entire reason to exist is "reports about a user" stays inside
`modules/users/reports/` no matter how many routes it grows; splitting it into a separate
top-level module just because the folder got large is the layer-based-folders mistake
`folder-structure.md` already bans, one level down.

## One module per feature folder

`modules/<feature>/<feature>.module.ts` — the module file lives at the top of its feature folder,
not nested under a `module/` subfolder. A feature that grows large enough to need internal
sub-modules (rare) nests them under its own folder with the same convention repeated one level
down, not flattened into the parent module's provider list.

## `AppModule`

The root module has no feature `controllers`/business `providers` of its own beyond what
`nest new` scaffolds (and those get deleted per `plan.md` step 2). Its `imports` array lists
`core/` modules first (Prisma, health, logger, and any of auth/queue/cache/storage/i18n that
were chosen), then every `modules/*` feature module, then the bot module if chosen.

**No inline `forRootAsync()` (or `forRoot()`) calls in `AppModule`'s `imports` array** — every
third-party module that needs config (`LoggerModule`, `I18nModule`, `ThrottlerModule`, etc.)
gets its own `core/<name>/<name>.module.ts` wrapper that calls `forRootAsync()` internally and
exports what needs to be exported, same as `PrismaModule` wraps `PrismaService`. `AppModule`
then imports the wrapper by name. This isn't just tidiness: a config factory inlined in
`AppModule` can't be unit-tested in isolation, and `AppModule`'s `imports` array stops being a
scannable list of "what does this app depend on" the moment even one entry is a multi-line
factory instead of a name.

```ts
// core/logger/logger.module.ts
@Module({
  imports: [
    NestLoggerModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => ({
        /* ... */
      }),
    }),
  ],
  exports: [NestLoggerModule],
})
export class LoggerModule {}
```

**One explicit exception**: the global cross-cutting providers wired via Nest's `APP_FILTER`/
`APP_GUARD`/`APP_INTERCEPTOR`/`APP_PIPE` injection tokens (`PrismaExceptionFilter` always; the
default `ThrottlerGuard` **only if REST was chosen**) *do* belong in `AppModule`'s `providers`
array — that's the only mechanism Nest offers for registering something globally through DI (as
opposed to `app.useGlobalFilters()` et al. in `main.ts`, which can't inject other providers).
This is not a violation of "root module only imports" so much as the one legitimate class of
provider that belongs at the root by construction. Don't extend this exception to anything
else — a feature-specific provider never ends up in `AppModule` just because it's convenient.

`BotThrottlerGuard` is **not** part of this exception — it's applied per-update-handler-class via
`@UseGuards()`, not globally, even in a bot-only app with no REST branch at all. See
`../architecture/transport-adapter.md`'s "Rate limiting" bullet under Bot for why one global
guard can't serve both an HTTP req/res pair and a bot update's context shape.

```ts
@Module({
  imports: [PrismaModule, HealthModule, UsersModule /* ... */],
  providers: [
    { provide: APP_FILTER, useClass: PrismaExceptionFilter },
    { provide: APP_GUARD, useClass: ThrottlerGuard }, // only if REST was chosen
  ],
})
export class AppModule {}
```

## Review Checklist

- [ ] `@Module()` fields in the order above; empty keys omitted rather than left as `[]`.
- [ ] Module file sits at the top of its feature folder.
- [ ] `AppModule` only imports — no stray providers/controllers of its own, and no inline
      `forRootAsync()`/`forRoot()` factory calls; each has its own `core/<name>/` wrapper.
- [ ] `exports` reviewed on every change to a module — no accidental surface growth.
- [ ] A controller file only handles routes under one path prefix — a second, unrelated
      sub-resource prefix growing inside the same controller class is a signal to split, not a
      reason to add a comment section divider inside the file.
- [ ] A new controller/service pair split out for a sub-resource is registered in the same
      module's `controllers`/`providers` arrays, not left unregistered or promoted to a new
      module without meeting the promotion bar above.
