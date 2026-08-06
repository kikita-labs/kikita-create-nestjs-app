# Auth

Present only because this project opted into authorization. Delete this file (and its
`core/README.md` row / `AGENTS.md` bullet) if that questionnaire answer was "no".

One fixed, battle-tested pattern — not a menu of options. Do not introduce sessions, a bare
non-rotating JWT, or an alternate strategy without an ADR (`../decisions/README.md`).

## Pattern

- **Access token**: short-lived (`JWT_ACCESS_TTL`, 5–15 min), signed with `JWT_ACCESS_SECRET`.
  Returned in the response body on login/refresh — **never** set as a cookie. The client holds
  it in memory and sends it as `Authorization: Bearer <token>`.
- **Refresh token**: long-lived (`JWT_REFRESH_TTL`), signed with `JWT_REFRESH_SECRET`. Set as an
  **httpOnly, `Secure`, `SameSite=Strict` cookie scoped to the `/v1/auth/refresh` path only** —
  never sent on any other request, so a stolen access token from an XSS on some other page can't
  be paired with it.
- **Rotation**: every call to `/auth/refresh` issues a brand-new refresh token and immediately
  invalidates the old one. Store only a hash (`argon2` or SHA-256, not the raw token) of the
  current valid refresh token per session in the `RefreshToken` Prisma model. A refresh request
  presenting an already-used/invalidated token is treated as a compromised session — revoke the
  whole session's chain, not just reject the one request.
- **CSRF**: `csrf-csrf` (not `csurf` — deprecated, unmaintained) protecting the `/auth/refresh`
  route and any other cookie-authenticated mutation. Not needed on routes that only accept the
  Bearer access token, since those aren't cookie-driven and browsers don't auto-attach a header.
- **Password hashing**: `argon2id` (via the `argon2` package), not `bcrypt` — current best
  practice default, memory-hard against GPU cracking. Never store or log a raw password.
- **Guards**: `JwtAuthGuard` validates the access token on protected routes
  (`@UseGuards(JwtAuthGuard)`), applied per-route/controller — a route with no guard is public by
  default, so protect explicitly. `RolesGuard` + `@Roles('admin')` for role-gated routes, checked
  after `JwtAuthGuard` in the guard chain.

```ts
@Controller({ path: 'auth', version: '1' })
export class AuthController {
  @Post('login')
  async login(@Body() dto: LoginDto, @Res({ passthrough: true }) res: Response) {
    const { accessToken, refreshToken } = await this.authService.login(dto);
    res.cookie('refresh_token', refreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      path: '/v1/auth/refresh',
    });
    return { accessToken };
  }
}
```

## Prisma model

```prisma
model RefreshToken {
  id        String   @id @default(uuid())
  userId    String
  tokenHash String
  createdAt DateTime @default(now())
  revokedAt DateTime?
  user      User     @relation(fields: [userId], references: [id])
}
```

## Review Checklist

- [ ] Access token never set as a cookie; refresh token never returned in a JSON body.
- [ ] Refresh cookie is `httpOnly` + `Secure` + `SameSite=Strict`, scoped to the refresh path.
- [ ] Refresh rotation implemented — reuse of an invalidated token revokes the session.
- [ ] `csrf-csrf` wired on the refresh route.
- [ ] Passwords hashed with `argon2id`, never logged or stored raw.
- [ ] Every protected route has an explicit guard — nothing relies on a global default-deny that
      doesn't actually exist in Nest.
