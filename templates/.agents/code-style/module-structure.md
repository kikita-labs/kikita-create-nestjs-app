# Module Structure

Every `*.module.ts` follows the same field order in its `@Module()` decorator — makes modules
scannable and diffs small when only one section changes:

```ts
@Module({
  imports: [PrismaModule, OtherFeatureModule],
  controllers: [UsersController], // omit entirely for a bot-only or broker-only module
  providers: [UsersService, UsersRepository],
  exports: [UsersService],
})
export class UsersModule {}
```

1. `imports` — other modules this one depends on, `core/` modules first, then other `modules/*`.
2. `controllers` — REST controllers, if this module has any. Omit the key if none (don't write
   `controllers: []`).
3. `providers` — services, guards, interceptors, and anything else DI-managed that's specific to
   this module. A bot's `updates/*.update.ts` classes are registered here too (Telegraf/Necord
   update classes are just injectables).
4. `exports` — the module's public surface, see `../architecture/module-boundaries.md`. Only
   list what another module is actually meant to consume.

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
