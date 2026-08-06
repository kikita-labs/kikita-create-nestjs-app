# Transport Adapter

This project's application type: {{APP_TYPE}}.

REST and bot are **not** architecturally different applications — they're two thin transport
layers sitting on top of the same `modules/*` business logic (see `folder-structure.md`). This
file is the boundary: what belongs in the transport layer vs what belongs in the shared service
underneath, plus the concrete conventions for whichever transport(s) this project uses.

## The boundary, either transport

- Transport layer (Controller / Update handler): parses/validates the incoming request/event
  shape (DTO + `ValidationPipe`), calls exactly one `modules/*` service method, maps the result
  to a response/reply. No business rules, no direct Prisma calls, no side effects beyond calling
  the service.
- `modules/*` service: everything else — business validation, persistence, side effects,
  orchestration across other services.

If "both" was chosen, the REST controller and the bot update handler for the same feature call
the identical service method — that's the whole point of keeping them thin.

## Bootstrap wiring (fixed defaults, regardless of application type)

`main.ts` always wires these, in this rough order — none of them are questionnaire-gated:

```ts
async function bootstrap() {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });
  const configService = app.get(ConfigService);

  app.useLogger(app.get(Logger)); // nestjs-pino
  app.enableShutdownHooks(); // without this, OnModuleDestroy (PrismaService) never fires on SIGTERM
  app.useGlobalPipes(
    new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, forbidUnknownValues: true, transform: true }),
  );
  app.useGlobalInterceptors(new ClassSerializerInterceptor(app.get(Reflector)));
  // PrismaExceptionFilter (and ThrottlerGuard, if REST/bot) are NOT registered here — they're
  // DI-managed APP_FILTER/APP_GUARD providers in AppModule instead, see code-style/module-structure.md
  // REST-only: app.enableVersioning(...), app.enableCors(...), SwaggerModule.setup(...)
  // Auth-only: app.use(cookieParser()), then doubleCsrfProtection scoped to /v1/auth/refresh
  //   — see core/auth.md's Wiring section for why cookieParser() must come before any guard.

  await app.listen(configService.getOrThrow<number>('PORT'));
}
```

- **`enableShutdownHooks()`** — see `core/README.md`'s Prisma entry; a container orchestrator
  sends SIGTERM on restart/scale-down, and without this call Nest never runs the lifecycle
  hooks that close the Prisma connection cleanly.
- **Global `ClassSerializerInterceptor`** — the fixed response-shaping default, see
  `code-style/dto-and-validation.md`'s "Response shape" section. Applies to every transport,
  REST and bot alike, whenever a DTO with `@Exclude()` fields is returned.
- **Global `PrismaExceptionFilter`** (`src/common/filters/prisma-exception.filter.ts`) — maps
  `PrismaClientKnownRequestError` codes to the matching Nest HTTP exception (`P2002` →
  `ConflictException`, `P2025` → `NotFoundException`, and so on for the codes the project
  actually hits). Without it a constraint violation surfaces as an unhandled 500. Error
  responses use Nest's default `HttpException` JSON shape — no custom envelope; the filter's
  job is making Prisma errors go through a real `HttpException` subclass so they follow that
  same shape instead of a generic 500. Registered as an `APP_FILTER` provider in `AppModule`
  (not `app.useGlobalFilters()` in `main.ts`) — see `code-style/module-structure.md`'s
  `AppModule` section for why global filters/guards go through DI instead.
- **`GET /health/live` + `GET /health/ready`** (`@nestjs/terminus`) — always wired, not gated by
  the questionnaire, always two separate routes, never merged. Liveness checks nothing external;
  readiness checks Prisma plus every external dependency actually chosen (Redis if
  BullMQ/caching, RabbitMQ if messaging). See `core/health.md` for why merging them is a
  restart-storm risk, not just a style preference.

<!-- SCAFFOLD: keep this section only if REST or both was chosen -->
## REST

- **Versioning**: Nest URI Versioning, fixed default — `app.enableVersioning({ type:
  VersioningType.URI, defaultVersion: '1' })` in `main.ts`. Routes read `/v1/users`, not
  `/users`. Bump the version on a breaking change to a route's contract; do not silently change
  behavior on an existing version.
- **DTOs**: every request body/query/params type is a `class-validator`-decorated DTO class,
  never an inline `interface`/type. `Update*Dto` extends `Create*Dto` via `PartialType`/
  `OmitType`/`PickType` from `@nestjs/swagger` — see `code-style/dto-and-validation.md`.
- **Swagger**: every controller has `@ApiTags()`; every route has `@ApiOperation()` and its
  response DTO declared via `@ApiResponse({ type: ... })`. Served at `/docs`, always on (not
  conditionally disabled in prod — an internal-only API still benefits from the interactive
  contract, and Swagger UI can be put behind the same auth as the rest of the API if it must not
  be public).
- **CORS**: configured once in `main.ts` from the `CORS_ORIGIN` env var (comma-separated
  allowlist) — never `app.enableCors()` with no options / a wildcard origin.
- **Guards**: `RolesGuard` (if auth was chosen) applied per-controller or per-route via
  `@Roles()`, not globally — a route with no `@Roles()` decorator is public by default, so
  every route that should require auth must say so explicitly with `@UseGuards(JwtAuthGuard)`.
- **Rate limiting**: `@nestjs/throttler`, keyed by IP by default (the standard case for a public
  REST API — a bot's per-user throttling below is a different key, don't conflate the two).
  Registered globally as an `APP_GUARD` provider in `AppModule`, same reasoning as
  `PrismaExceptionFilter` above — not `app.useGlobalGuards()` in `main.ts`.

<!-- SCAFFOLD: keep this section only if bot or both was chosen -->
## Bot

Platform for this project: {{BOT_PLATFORM}}.

- **Generic pattern**: an incoming platform event (message, command, interaction) is handled by
  one `updates/*.update.ts` file per logical command/event, which validates the payload (DTO +
  `ValidationPipe` works the same way here as in a controller — Nest's pipes aren't
  HTTP-specific), calls one `modules/*` service method, and sends the reply through the
  platform's own reply mechanism (`ctx.reply()` for Telegraf, an interaction response for
  Discord).
- **Rate limiting**: keyed by the platform's user/chat id, not IP — a bot has no meaningful
  per-request IP. Implement as a guard extending `ThrottlerGuard`, overriding
  `getRequestResponse()` to pull the id off the platform context (not off an HTTP req/res pair
  that doesn't exist) and `getTracker()` to return it. Applied via `@UseGuards(BotThrottlerGuard)`
  directly on update-handler classes — **not** registered as a global `APP_GUARD`, unlike the
  REST branch's default `ThrottlerGuard` above. One guard can't cleanly handle both an HTTP
  req/res pair and a bot update's context shape, and a bot-only app (no REST branch at all)
  registering `ThrottlerGuard` globally would apply the wrong (IP-based) guard to every update.

  **Mandatory, not optional**: also override `onModuleInit()` to force
  `this.commonOptions.setHeaders = false` after calling `super.onModuleInit()`, scoped to this
  guard subclass — not the shared `ThrottlerModule.forRoot()` config, which a REST branch (if
  the app has one) still wants real headers from. Without this, `ThrottlerGuard.handleRequest()`
  unconditionally calls `res.header(...)` (the library default), and since a bot update's fake
  `res` here is `{}`, that throws `TypeError: res.header is not a function` on **every single
  guarded update** — a crash that a build, a lint pass, and a unit test that only instantiates
  the guard (never calls `canActivate()`) all miss completely. Write the guard's test to actually
  call `canActivate()` with a constructed `ExecutionContext`, not just construct the class.

  ```ts
  @Injectable()
  export class BotThrottlerGuard extends ThrottlerGuard {
    async onModuleInit(): Promise<void> {
      await super.onModuleInit();
      this.commonOptions.setHeaders = false;
    }

    protected getRequestResponse(context: ExecutionContext) {
      return { req: context.getArgByIndex(0), res: {} };
    }

    protected getTracker(req: Context): Promise<string> {
      return Promise.resolve(String(req.from?.id ?? 'anonymous'));
    }
  }
  ```
- **Multi-step flows**: Telegraf's `Scenes`/`WizardScene` or the equivalent construct on another
  platform. Keep scene state minimal (IDs, not full entities) and always have a cancel/timeout
  path — a stuck scene must not become the only way to interact with the bot.

<!-- SCAFFOLD: keep this Telegram sub-block only if platform = Telegram -->
### Telegram (`nestjs-telegraf`)

**`TelegrafModule.forRootAsync()` calls `bot.launch()` automatically** as soon as the module
initializes — there is no separate "start polling" step to opt into, and no way to construct the
module without it short of `launchOptions: false`. This makes the bot immediately start
long-polling (or webhook-listening) the real Telegram API the moment `AppModule` boots, which is
never what you want when `NODE_ENV=test` (a test run, e2e or otherwise, has no business making
outbound calls to Telegram) or in any environment without a real, working
`TELEGRAM_BOT_TOKEN`. Gate it:

```ts
// bot/bot.module.ts
TelegrafModule.forRootAsync({
  inject: [ConfigService],
  useFactory: (configService: ConfigService) => ({
    token: configService.getOrThrow<string>('TELEGRAM_BOT_TOKEN'),
    launchOptions: configService.get<string>('NODE_ENV') === 'test' ? false : undefined,
  }),
}),
```

```ts
@Update()
export class StartUpdate {
  constructor(private readonly usersService: UsersService) {}

  @Start()
  async onStart(@Ctx() ctx: Context): Promise<void> {
    await this.usersService.upsertFromTelegram(ctx.from);
    await ctx.reply('Welcome.');
  }
}
```

**Import gotcha**: current `telegraf` majors restrict which subpaths resolve via `package.json`
`exports` — a deep import like `telegraf/typings/core/types/typegram` (from an older example
found online) no longer resolves; use `telegraf/types` instead. Verify against the installed
version's actual `exports` map if a type import 404s, rather than assuming an old blog post's
import path still works.

<!-- SCAFFOLD: keep only if i18n was chosen -->
**With i18n**: `nestjs-telegraf-i18n` needs its module imported alongside `TelegrafModule` and
its middleware wired in, plus a custom context type so `ctx.t()`/`ctx.tReply()` are available in
update handlers — see `core/i18n.md`'s Telegram section for the exact wiring, it's more than
just installing the package.

<!-- SCAFFOLD: keep this Discord sub-block only if platform = Discord -->
### Discord (`necord`)

```ts
@Injectable()
export class PingCommand {
  constructor(private readonly usersService: UsersService) {}

  @SlashCommand({ name: 'ping', description: 'Health check' })
  async onPing(@Context() [interaction]: SlashCommandContext): Promise<void> {
    await interaction.reply('pong');
  }
}
```

<!-- SCAFFOLD: keep this sub-block only if platform = "another platform" -->
### {{BOT_PLATFORM}} (custom adapter)

No prewritten adapter ships in this skill for this platform. Follow the generic pattern above:
one handler per command/event under `bot/updates/`, DTO-validated input, a single call into
`modules/*`. Document the platform library's specific decorator/context shape here once written,
so the pattern is discoverable for the next feature instead of re-derived from scratch.

## Review Checklist

- [ ] No business logic inline in a controller/update handler — one call into `modules/*`.
- [ ] `main.ts` has `enableShutdownHooks()` and the global `ClassSerializerInterceptor`; the
      global `PrismaExceptionFilter`/`ThrottlerGuard` are `APP_FILTER`/`APP_GUARD` providers in
      `AppModule`, not also (or instead) wired in `main.ts`.
- [ ] `GET /health/live` and `GET /health/ready` are two separate routes; only `/ready` checks
      Prisma connectivity (and Redis/RabbitMQ if those were chosen).
- [ ] REST: every route versioned (`/v1/...`), every DTO `class-validator`-decorated, Swagger
      annotations present, CORS from env allowlist, `ThrottlerGuard` wired.
- [ ] Bot: every handler under `updates/`, rate-limited by user/chat id, scenes have a
      cancel/timeout path.
- [ ] "Both" chosen: REST and bot handlers for the same feature call the identical service
      method, no duplicated logic.
