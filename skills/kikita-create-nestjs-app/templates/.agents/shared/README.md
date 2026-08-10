# Shared

Registry of everything in `src/common/` meant to be reused across modules: generic pipes,
filters, interceptors, decorators, and framework-agnostic utilities.

- `common/pipes/`, `common/filters/`, `common/interceptors/`, `common/decorators/` —
  Nest-decorated, cross-cutting pieces (e.g. a custom validation pipe, a global exception filter,
  a `@CurrentUser()` param decorator).
- `common/utilities/` — plain functions/classes. Zero `@nestjs/*` imports, ever (enforced by the
  ESLint restricted-import rule, see `../architecture/README.md`).

Check this file before building something new; reuse before you build.

## Registry

| Name | Kind | Path | Doc | Summary |
| --- | --- | --- | --- | --- |
| PrismaExceptionFilter | filter | `common/filters/` | — | Global `APP_FILTER`, maps `PrismaClientKnownRequestError` codes to the matching Nest HTTP exception. Always present, not questionnaire-gated. See `../architecture/transport-adapter.md`. |

Kind is one of: `pipe`, `filter`, `interceptor`, `decorator`, `utility`.

## Adding an entry

1. Build it under the matching `src/common/` subfolder (verify a `utility` genuinely has no
   `@nestjs/*` import before placing it there).
2. Add a row to the table above.
3. If it has a non-trivial API (e.g. an interceptor's configurable options, a pipe's error
   shape), create `.agents/shared/<name>.md` describing what it's for, its public API, and when
   to use it vs. building something new. Link it in the Doc column.
4. If it's a small utility with no meaningful API surface, the table row alone is enough.

This applies every time a shared piece is added, changed, or removed — see `../documentation.md`.

## Review Checklist

- [ ] Table has no stale entries (removed) or missing entries (new shared piece not listed).
- [ ] Each non-trivial entry has its own doc file, linked from the table.
- [ ] `Kind` column filled in for every row.
- [ ] Nothing under `common/utilities/` imports `@nestjs/*`.
