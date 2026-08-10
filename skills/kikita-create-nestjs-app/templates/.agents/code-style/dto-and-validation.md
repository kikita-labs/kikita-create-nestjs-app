# DTOs & Validation

Two validation tools, two different jobs — never blur the line:

- **`class-validator` + `class-transformer`** — the HTTP/bot input layer. Every DTO class is
  decorated, and the global `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`,
  `forbidUnknownValues`, `transform` all `true`) does the enforcement. Never write a manual
  `if (!dto.email) throw ...` check that duplicates what a decorator already does.
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
// core/config/env.schema.ts — the one file allowed to read process.env directly
export const envSchema = z.object({
  DATABASE_URL: z.url(), // z.string().url() is deprecated as of zod 4 — use the top-level z.url()
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

**This is the part that's easy to get silently wrong**: `ClassSerializerInterceptor` only strips
`@Exclude()` fields off an actual **instance of the class**. It does nothing for a plain object
that merely has a TypeScript return type annotation claiming to be that class — TypeScript types
don't exist at runtime, so `@Exclude()` never runs, and the field goes out over the wire intact.
This controller compiles cleanly, passes review at a glance, and leaks the password hash on every
request:

```ts
// WRONG — compiles, "looks" correct, leaks passwordHash: the return value is a plain Prisma
// object, never actually instantiated as UserResponseDto, so @Exclude() has nothing to strip.
async findOne(id: string): Promise<UserResponseDto> {
  return this.usersService.findOne(id); // returns the raw Prisma User row
}
```

The controller (or service, at the boundary where the DTO is returned) must explicitly convert
the plain object into a real instance with `plainToInstance` before returning it:

```ts
// CORRECT
async findOne(id: string): Promise<UserResponseDto> {
  const user = await this.usersService.findOne(id);
  return plainToInstance(UserResponseDto, user, { excludeExtraneousValues: true });
}
```

`excludeExtraneousValues: true` also means every field meant to survive needs `@Expose()` (or a
consistent project-wide choice of exclude-by-default vs expose-by-default — pick one and follow
it in every DTO, don't mix). A test asserting the sensitive field is actually absent from a real
serialized response (not just present-with-`@Exclude()`-in-the-source) is what catches a
regression here — see `../testing-and-quality.md`.

## Review Checklist

- [ ] Every DTO field has a `class-validator` decorator matching its actual constraint.
- [ ] Every nested-object/array-of-objects DTO field has both `@ValidateNested()` and
      `@Type(() => NestedDto)` — not just one.
- [ ] `Update*Dto` derived from `Create*Dto` via `PartialType`/`OmitType`/`PickType` from
      `@nestjs/swagger`, not `@nestjs/mapped-types`.
- [ ] No env var read directly from `process.env` outside the Zod-validated config module.
- [ ] No raw Prisma entity returned directly from a controller/update handler — a DTO with
      `@Exclude()`/`@Expose()` fields, actually instantiated via `plainToInstance(...,
      { excludeExtraneousValues: true })`, not just type-annotated as the DTO. A return type
      claiming `UserResponseDto` with no `plainToInstance` call anywhere in the method is the
      bug this checklist item exists to catch.
- [ ] At least one test asserts a sensitive field is actually absent from a real serialized
      response for every DTO that has an `@Exclude()`d field.
