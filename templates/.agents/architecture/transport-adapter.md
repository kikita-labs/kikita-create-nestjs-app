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
  per-request IP. Implement as a guard reading the id off the platform context, reusing the same
  `@nestjs/throttler` package with a custom `getTracker()`.
- **Multi-step flows**: Telegraf's `Scenes`/`WizardScene` or the equivalent construct on another
  platform. Keep scene state minimal (IDs, not full entities) and always have a cancel/timeout
  path — a stuck scene must not become the only way to interact with the bot.

<!-- SCAFFOLD: keep this Telegram sub-block only if platform = Telegram -->
### Telegram (`nestjs-telegraf`)

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
- [ ] REST: every route versioned (`/v1/...`), every DTO `class-validator`-decorated, Swagger
      annotations present, CORS from env allowlist.
- [ ] Bot: every handler under `updates/`, rate-limited by user/chat id, scenes have a
      cancel/timeout path.
- [ ] "Both" chosen: REST and bot handlers for the same feature call the identical service
      method, no duplicated logic.
