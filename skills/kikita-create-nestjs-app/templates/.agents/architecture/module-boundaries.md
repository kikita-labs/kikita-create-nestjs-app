# Module Boundaries

A `modules/<feature>/*.module.ts` file declares its public surface through `exports` — anything
not exported is that feature's private implementation detail, even though TypeScript's module
system would technically let another file import it directly via a relative path (blocked by the
ESLint restricted-import rule in `README.md`, not by the language itself). Capability folders
inside a feature are organizational by default; they become an additional Nest boundary only
when they contain their own `*.module.ts` and are imported by the parent feature module.

```ts
@Module({
  imports: [PrismaModule],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService], // the only thing another module is allowed to depend on
})
export class UsersModule {}
```

## Cross-module dependencies

- A feature module may import another feature module's `*Module` and inject its exported
  service — that's the sanctioned way to reuse another feature's logic (e.g. `OrdersModule`
  injecting `UsersService` from `UsersModule`).
- A feature module must never import another feature's controller, DTO meant to stay internal,
  or Prisma-adjacent repository helper directly — only what's in `exports`.
- Code in one top-level feature must not reach into another feature's capability folders or
  private files. Expose a narrow provider from the owning feature module, or move genuinely
  cross-feature logic to `common/` or a true app-wide `core/` singleton.
- `core/` providers (Prisma, auth, logger, queue, cache, storage) are typically global
  (`@Global()` module or re-exported from `AppModule`) — every feature module can inject them
  without explicitly importing the core module, since they're true app-wide singletons. Don't
  make a `modules/*` service `@Global()` — that's reserved for `core/`.
- Circular module imports (`A` imports `B` imports `A`) are a design smell, not a Nest
  limitation to work around with `forwardRef()`. Reach for `forwardRef()` only as a last resort
  and leave a comment explaining why the cycle is unavoidable; otherwise extract the shared piece
  both modules need into `core/` or a third module.

## Review Checklist

- [ ] Every module's `exports` array only lists what other modules genuinely need.
- [ ] No feature module reaches into another feature's DTO/controller/repository directly.
- [ ] No cross-feature import reaches into a capability folder or other private implementation
      path.
- [ ] No new `forwardRef()` without a comment explaining why the cycle exists.
- [ ] Nothing under `modules/*` is marked `@Global()`.
