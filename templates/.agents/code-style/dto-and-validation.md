# DTOs & Validation

Two validation tools, two different jobs — never blur the line:

- **`class-validator` + `class-transformer`** — the HTTP/bot input layer. Every DTO class is
  decorated, and the global `ValidationPipe` (`whitelist: true, forbidNonWhitelisted: true,
  transform: true`) does the enforcement. Never write a manual `if (!dto.email) throw ...` check
  that duplicates what a decorator already does.
- **Zod** — env/config validation only, via `ConfigModule.forRoot({ validate })`. Env var errors
  surface at boot ("`DATABASE_URL`: Expected string, received undefined") instead of failing
  confusingly on first use in production.

```ts
export class CreateUserDto {
  @IsEmail()
  email!: string;

  @IsString()
  @MinLength(8)
  password!: string;
}
```

```ts
// config/env.schema.ts
export const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().default(3000),
  CORS_ORIGIN: z.string(),
});

export function validate(config: Record<string, unknown>) {
  return envSchema.parse(config);
}
```

## DTO reuse: `PartialType`/`OmitType`/`PickType`

Derive update/response DTOs from the create DTO instead of redeclaring fields.

```ts
export class UpdateUserDto extends PartialType(OmitType(CreateUserDto, ['password'] as const)) {}
```

**Gotcha, always import these from `@nestjs/swagger`, never from `@nestjs/mapped-types`**: this
project always has Swagger wired (fixed default, see `SKILL.md`), and `@nestjs/mapped-types`'s
versions of `PartialType`/`OmitType`/`PickType` silently drop the `@ApiProperty` metadata the
`@nestjs/swagger` versions carry forward — the generated OpenAPI schema for the derived DTO ends
up wrong (missing fields, missing descriptions) with no error or warning. Both packages export
functions with the identical name and signature, so the wrong import doesn't fail type-checking
— it just quietly breaks the Swagger doc.

```ts
// Correct
import { OmitType, PartialType } from '@nestjs/swagger';

// Wrong — compiles fine, breaks the generated Swagger schema silently
import { OmitType, PartialType } from '@nestjs/mapped-types';
```

## Response shape

Controllers/update handlers return a DTO class (or a Prisma model type mapped to one), never the
raw Prisma entity — a raw entity leaks columns (password hashes, internal flags) that were never
meant to cross the transport boundary. Use `class-transformer`'s `@Exclude()`/`@Expose()` plus a
global `ClassSerializerInterceptor`, or an explicit mapping function, consistently across the
project — pick one approach and document the choice here once made.

## Review Checklist

- [ ] Every DTO field has a `class-validator` decorator matching its actual constraint.
- [ ] `Update*Dto` derived from `Create*Dto` via `PartialType`/`OmitType`/`PickType` from
      `@nestjs/swagger`, not `@nestjs/mapped-types`.
- [ ] No env var read directly from `process.env` outside the Zod-validated config module.
- [ ] No raw Prisma entity returned directly from a controller/update handler.
