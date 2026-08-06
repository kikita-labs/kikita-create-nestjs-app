# Health Checks

Always present, not questionnaire-gated — a deployable service needs this from day one. Uses
`@nestjs/terminus`.

## Two endpoints, not one — liveness and readiness are different questions

- **`GET /health/live`** — "is the process itself alive, or does it need to be killed and
  restarted?" Checks nothing external: no Prisma, no Redis, no RabbitMQ. A liveness probe that
  pings the database is a common, well-documented anti-pattern — if Postgres has a brief blip,
  every replica's liveness probe fails at once, the orchestrator kills and restarts every pod
  simultaneously, and a transient DB hiccup turns into a full outage plus a thundering-herd
  reconnect storm on top of it. Liveness only checks things a **restart of this process** could
  actually fix (event loop responsiveness, memory pressure) — not things a restart does nothing
  for.
- **`GET /health/ready`** — "can this instance actually serve a request right now?" Checks every
  external dependency the app needs to function: Prisma always, plus Redis if BullMQ/caching was
  chosen, plus RabbitMQ if messaging was chosen. This is what an orchestrator uses to decide
  whether to route traffic to this instance — a failed readiness check pulls the pod out of the
  load-balancer rotation without killing it, which is the correct reaction to "my dependency is
  temporarily down."

Never merge these into a single `GET /health` — that's the mistake this file exists to prevent
mid-scaffold. If a project's deploy target has no orchestrator wired yet, both endpoints still
exist; they're just not called by anything until one is.

```ts
@Controller({ path: 'health', version: '1' })
export class HealthController {
  constructor(
    private readonly health: HealthCheckService,
    private readonly prisma: PrismaHealthIndicator, // core/health/indicators/prisma.health-indicator.ts
    // + one indicator per chosen dependency, e.g. RedisHealthIndicator, RabbitMQHealthIndicator
  ) {}

  @Get('live')
  @HealthCheck()
  liveness() {
    return this.health.check([]); // process is up and answering HTTP — that's the whole check
  }

  @Get('ready')
  @HealthCheck()
  readiness() {
    return this.health.check([
      () => this.prisma.isHealthy('prisma'),
      // one line per chosen dependency's indicator
    ]);
  }
}
```

## Indicators

One `*.health-indicator.ts` per external dependency, under `core/health/indicators/`:

```ts
// core/health/indicators/prisma.health-indicator.ts
@Injectable()
export class PrismaHealthIndicator extends HealthIndicator {
  constructor(private readonly prisma: PrismaService) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return this.getStatus(key, true);
    } catch (error) {
      throw new HealthCheckError('Prisma check failed', this.getStatus(key, false));
    }
  }
}
```

Add a `RedisHealthIndicator`/`RabbitMQHealthIndicator` the same shape when those features are
chosen — a lightweight connectivity check (ping/status call), not a full round-trip through
business logic.

## Both routes are unauthenticated and unversioned-in-practice

`/health/live` and `/health/ready` are excluded from any auth guard (an orchestrator has no
credentials to send) and, while they still sit behind the app's URI versioning prefix like every
other route for consistency, they're never referenced with a version number in deploy configs —
point infra config at whatever the current default version resolves to.

## Review Checklist

- [ ] `/health/live` checks nothing external — restarting the process is the only remedy it
      implies.
- [ ] `/health/ready` checks every external dependency actually wired (Prisma always, Redis/
      RabbitMQ if chosen) — not a subset, not "just Prisma because that's what shipped first".
- [ ] Both routes excluded from auth guards.
- [ ] A dependency added later (a new external service) gets its own indicator added to
      `/health/ready` in the same change — see `../documentation.md`.
