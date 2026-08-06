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

## Nested DTOs

A field that's itself an object or array of objects needs both `@ValidateNested()` **and**
`@Type(() => NestedDto)` — not just one of the two. `class-validator` only descends into a
nested value if `class-transformer` actually turned it into an instance of the nested class
first, and `@Type()` is what tells `class-transformer` which class to instantiate. Missing
`@Type()` is a silent failure, same class of bug as the `@nestjs/mapped-types` gotcha below: the
outer DTO validates fine, the nested object's constraints never run, and nothing errors.

```ts
export class CreateOrderDto {
  @ValidateNested()
  @Type(() => AddressDto)
  shippingAddress!: AddressDto;

  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items!: OrderItemDto[];
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

## Response shape (fixed default: global `ClassSerializerInterceptor`)

Controllers/update handlers return a DTO class (or a Prisma model type mapped to one), never the
raw Prisma entity — a raw entity leaks columns (password hashes, internal flags) that were never
meant to cross the transport boundary.

The fixed pattern, wired once in `main.ts` (see `../architecture/transport-adapter.md`'s
bootstrap section) and never re-decided per feature: a global `ClassSerializerInterceptor`
strips any field marked `@Exclude()` on the class actually returned. No competing approach (a
hand-written mapping function, a second serialization library) gets introduced without an ADR —
one mechanism, applied everywhere, is what makes "did I leak the password hash" a single
property of the class definition instead of something reviewed per endpoint.

```ts
export class UserResponseDto {
  id!: string;
  email!: string;

  @Exclude()
  passwordHash!: string;
}
```

```ts
// main.ts
app.useGlobalInterceptors(new ClassSerializerInterceptor(app.get(Reflector)));
```

A service method can still return the Prisma entity directly to the controller — the
interceptor only serializes what actually leaves the transport boundary — but the type the
controller method's return type claims must be the DTO, not the Prisma model, so the exclusion
is enforced by the type system too, not only by the interceptor at runtime.

## Review Checklist

- [ ] Every DTO field has a `class-validator` decorator matching its actual constraint.
- [ ] Every nested-object/array-of-objects DTO field has both `@ValidateNested()` and
      `@Type(() => NestedDto)` — not just one.
- [ ] `Update*Dto` derived from `Create*Dto` via `PartialType`/`OmitType`/`PickType` from
      `@nestjs/swagger`, not `@nestjs/mapped-types`.
- [ ] No env var read directly from `process.env` outside the Zod-validated config module.
- [ ] No raw Prisma entity returned directly from a controller/update handler — a DTO with
      `@Exclude()` on sensitive fields, relying on the global `ClassSerializerInterceptor`.
