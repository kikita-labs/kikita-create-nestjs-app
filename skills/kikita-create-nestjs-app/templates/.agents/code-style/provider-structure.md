# Provider Structure

Applies to services, controllers, guards, interceptors, and any other injectable class.

## Dependency injection

- Constructor injection only. No property injection (`@Inject()` on a class field), no service
  locator (`ModuleRef.get()`) unless there's a genuine circular-dependency or dynamic-lookup
  reason — document it inline if so.
- Constructor parameters are `private readonly` (or `protected readonly` if a subclass needs
  access), typed explicitly — never rely on inference from a default.
- Order constructor parameters from most-specific (this module's own dependencies) to
  least-specific (cross-cutting `core/` singletons like `PrismaService`, loggers) — keeps the
  "what does this class actually need" signal near the top.

```ts
@Injectable()
export class UsersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly logger: Logger,
  ) {}
}
```

## Member order

1. Static members (rare — a static factory, a constant).
2. Instance fields (only for state that isn't a DI dependency — most services have none).
3. Constructor.
4. Public methods, in the order a consumer would call them (e.g. `create`, `findAll`,
   `findOne`, `update`, `remove` for a standard CRUD service — matches REST verb order, and a
   bot update handler follows the same "most common action first" logic).
5. Private/protected helper methods, placed directly below the public method that uses them —
   not all grouped at the bottom of the class.

## Controllers and update handlers stay thin

A controller method or bot update handler does three things: validate input (via the DTO +
`ValidationPipe`, not manual checks), call one service method, shape the response. See
`../architecture/transport-adapter.md` for the full boundary. If a controller method has an
`if`/`for`/try-catch doing real work beyond that, the logic belongs in the service.

```ts
@Post()
async create(@Body() dto: CreateUserDto): Promise<UserResponseDto> {
  return this.usersService.create(dto);
}
```

## Body formatting

Same rules as `kikita-create-angular-app`'s `component-structure.md`, applied to service/
controller/guard method bodies — this isn't left unstated just because the framework differs:

- Group statements by purpose; blank line between groups, not inside one.
- Blank line before and after every `if` block.
- Collapse a single-statement `if` onto one line: `if (!user) throw new NotFoundException();`.
- Exception: a run of consecutive single-line guard `if`s (same shape, one condition/throw each,
  no other statements between them) stays tight — no blank line between them, only before the
  first and after the last. The tight run reads as one decision table, not separate blocks.
- Blank line before `return`.

```ts
async update(id: string, dto: UpdateUserDto): Promise<User> {
  const existing = await this.prisma.user.findUnique({ where: { id } });

  if (!existing) throw new NotFoundException();
  if (existing.deletedAt) throw new GoneException();

  const updated = await this.prisma.user.update({ where: { id }, data: dto });
  this.logger.log(`Updated user ${id}`);

  return updated;
}
```

## Exceptions

Throw Nest's built-in HTTP exceptions (`NotFoundException`, `BadRequestException`,
`ConflictException`, ...) from the service layer, not the controller — the exception carries the
right HTTP status regardless of which transport calls the service, and a bot update handler
catches the same exception type to format a platform-appropriate error message instead of
leaking an HTTP-shaped error object into a chat reply.

## Review Checklist

- [ ] Constructor injection only, params `private readonly`, typed explicitly.
- [ ] Member order follows the sequence above.
- [ ] Blank line before/after `if` blocks (except tight guard-clause runs) and before `return`.
- [ ] Controller/update-handler methods contain no business logic — one service call.
- [ ] Exceptions thrown from the service layer using Nest's built-in HTTP exception classes.
