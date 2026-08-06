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
controller file, in the same module, the moment a feature grows a sub-resource with its own
route prefix — don't grow one controller class into a dumping ground for every route that
happens to touch the same Prisma model.

Concretely, for a `users` feature that grows a `/v1/users/reports/unresolved`-style surface:

```
modules/users/
  users.module.ts
  users.controller.ts          <- /v1/users, /v1/users/:id (base CRUD)
  user-reports.controller.ts   <- /v1/users/reports/... (sub-resource)
  users.service.ts
  user-reports.service.ts      <- only if the sub-resource's logic is non-trivial, see below
  enums/
    users-routes.enum.ts        <- path segments, see below
  dto/
    create-user.dto.ts
    update-user.dto.ts
    user-report-query.dto.ts
```

Path segments are enum members, not repeated string literals — see
`../architecture/transport-adapter.md`'s "Route paths" bullet:

```ts
// modules/users/enums/users-routes.enum.ts
export enum UsersRoutes {
  Base = 'users',
  ReportsBase = 'users/reports',
  Unresolved = 'unresolved',
}
```

```ts
@Controller({ path: UsersRoutes.Base, version: '1' })
export class UsersController {
  constructor(private readonly usersService: UsersService) {}
  // GET /v1/users, GET /v1/users/:id, POST /v1/users, ...
}

@Controller({ path: UsersRoutes.ReportsBase, version: '1' })
export class UserReportsController {
  constructor(private readonly userReportsService: UserReportsService) {}

  @Get(UsersRoutes.Unresolved)
  findUnresolved(): Promise<UserReportResponseDto[]> {
    return this.userReportsService.findUnresolved();
  }
}
```

```ts
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

**When to promote the sub-resource to its own top-level module instead of a second controller
in `users/`**: only when it stops being genuinely user-scoped — e.g. a `reports` concern that
spans multiple unrelated features, not just users, belongs in its own `modules/reports/` from
the start. A sub-resource whose entire reason to exist is "reports about a user" stays inside
`modules/users/` no matter how many routes it grows; splitting it into a separate module just
because the file got long is the layer-based-folders mistake `folder-structure.md` already bans,
one level down.

## One module per feature folder

`modules/<feature>/<feature>.module.ts` — the module file lives at the top of its feature folder,
not nested under a `module/` subfolder. A feature that grows large enough to need internal
sub-modules (rare) nests them under its own folder with the same convention repeated one level
down, not flattened into the parent module's provider list.

## `AppModule`

The root module has no feature `controllers`/business `providers` of its own beyond what
`nest new` scaffolds (and those get deleted per `plan.md` step 2). Its `imports` array lists
`core/` modules first (Prisma, health, logger, and any of auth/queue/cache/storage that were
chosen), then every `modules/*` feature module, then the bot module if chosen.

**One explicit exception**: the global cross-cutting providers wired via Nest's `APP_FILTER`/
`APP_GUARD`/`APP_INTERCEPTOR`/`APP_PIPE` injection tokens (`PrismaExceptionFilter`, the
`ThrottlerGuard` if REST/bot was chosen) *do* belong in `AppModule`'s `providers` array — that's
the only mechanism Nest offers for registering something globally through DI (as opposed to
`app.useGlobalFilters()` et al. in `main.ts`, which can't inject other providers). This is not a
violation of "root module only imports" so much as the one legitimate class of provider that
belongs at the root by construction. Don't extend this exception to anything else — a
feature-specific provider never ends up in `AppModule` just because it's convenient.

```ts
@Module({
  imports: [PrismaModule, HealthModule, UsersModule /* ... */],
  providers: [
    { provide: APP_FILTER, useClass: PrismaExceptionFilter },
    { provide: APP_GUARD, useClass: ThrottlerGuard }, // only if REST or bot was chosen
  ],
})
export class AppModule {}
```

## Review Checklist

- [ ] `@Module()` fields in the order above; empty keys omitted rather than left as `[]`.
- [ ] Module file sits at the top of its feature folder.
- [ ] `AppModule` only imports — no stray providers/controllers of its own.
- [ ] `exports` reviewed on every change to a module — no accidental surface growth.
- [ ] A controller file only handles routes under one path prefix — a second, unrelated
      sub-resource prefix growing inside the same controller class is a signal to split, not a
      reason to add a comment section divider inside the file.
- [ ] A new controller/service pair split out for a sub-resource is registered in the same
      module's `controllers`/`providers` arrays, not left unregistered or promoted to a new
      module without meeting the promotion bar above.
