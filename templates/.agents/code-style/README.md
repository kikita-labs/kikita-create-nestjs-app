# Code Style

How code is written and formatted in this project. Prettier owns whitespace/formatting; ESLint
owns correctness and code-quality rules. Don't hand-format around Prettier.

- [imports.md](./imports.md) — import grouping and ordering.
- [provider-structure.md](./provider-structure.md) — class member order, constructor DI,
  visibility.
- [dto-and-validation.md](./dto-and-validation.md) — `class-validator`/`class-transformer` on
  DTOs, Zod on config, the `PartialType`/`OmitType`/`PickType` reuse pattern.
- [module-structure.md](./module-structure.md) — what goes in a `*.module.ts`, ordering of
  `imports`/`controllers`/`providers`/`exports`.

Adding a new code-style doc: only when a rule doesn't fit naturally into one of the above. Link
it here immediately.

If the user changes or corrects a code-style rule (import order, member order, formatting,
DTO conventions — anything above), update the matching file in the same change, right when they
say it — don't wait for the same correction to happen twice. See `../documentation.md`.
