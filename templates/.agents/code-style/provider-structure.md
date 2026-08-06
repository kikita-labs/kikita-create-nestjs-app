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

## Exceptions

Throw Nest's built-in HTTP exceptions (`NotFoundException`, `BadRequestException`,
`ConflictException`, ...) from the service layer, not the controller — the exception carries the
right HTTP status regardless of which transport calls the service, and a bot update handler
catches the same exception type to format a platform-appropriate error message instead of
leaking an HTTP-shaped error object into a chat reply.

## Review Checklist

- [ ] Constructor injection only, params `private readonly`, typed explicitly.
- [ ] Member order follows the sequence above.
- [ ] Controller/update-handler methods contain no business logic — one service call.
- [ ] Exceptions thrown from the service layer using Nest's built-in HTTP exception classes.
