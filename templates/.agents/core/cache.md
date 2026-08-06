# Cache

Present only because this project opted into caching. Delete this file (and its `core/README.md`
row / `AGENTS.md` bullet) if that questionnaire answer was "no".

`@nestjs/cache-manager` + `@keyv/redis` against the same Redis instance used by the queue (if
both were chosen — one Redis, two use cases). Cache-aside pattern: read cache first, fall back to
the real source (Prisma) on miss, write the result back with a TTL. Do not reach for caching
speculatively on every endpoint — add it where a real latency/load problem shows up.

```ts
// core/cache/cache.module.ts
@Module({
  imports: [
    CacheModule.registerAsync({
      isGlobal: true,
      useFactory: () => ({
        stores: [new Keyv({ store: new KeyvRedis(process.env.REDIS_URL) })],
        ttl: Number(process.env.CACHE_TTL_SECONDS ?? 60) * 1000,
      }),
    }),
  ],
})
export class CacheModule {}
```

```ts
async findOne(id: string): Promise<User> {
  const cached = await this.cache.get<User>(`user:${id}`);
  if (cached) return cached;

  const user = await this.prisma.user.findUniqueOrThrow({ where: { id } });
  await this.cache.set(`user:${id}`, user);
  return user;
}
```

## Conventions

- Cache keys are namespaced (`<entity>:<id>`, `<entity>:list:<hash-of-query>`) — never a bare id
  that could collide across entity types.
- Every cache write has an explicit TTL (`CACHE_TTL_SECONDS`, short by default) — no unbounded
  entries. Start short, extend only once real usage patterns justify it.
- Invalidate explicitly on write: a `create`/`update`/`remove` that touches a cached entity
  deletes (or overwrites) the corresponding cache key(s) in the same service method — don't rely
  on TTL expiry alone for correctness-sensitive data.

## Review Checklist

- [ ] Every cached read has a documented invalidation path for the writes that affect it.
- [ ] Cache keys namespaced, no bare-id collisions across entity types.
- [ ] TTL set explicitly on every write.
- [ ] Caching added because of a measured need, not speculatively on every new endpoint.
