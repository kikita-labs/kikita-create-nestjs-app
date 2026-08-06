# Testing & Quality Gate

Tests configured for this project: {{TESTS}}. Package manager: {{PACKAGE_MANAGER}}.

## Before every push

1. `{{PACKAGE_MANAGER}} run lint` — zero errors. Warnings should be fixed, not suppressed,
   unless there's a documented reason.
2. `{{PACKAGE_MANAGER}} run format:check` — Prettier owns formatting; run
   `{{PACKAGE_MANAGER}} run format` to fix.
3. If tests are configured: `{{PACKAGE_MANAGER}} run test` (unit) and/or
   `{{PACKAGE_MANAGER}} run test:e2e` (Supertest, plus Testcontainers if "both" was chosen) —
   all green.

Do not push with a failing lint, format check, or test suite. If a check can't pass and you
don't know why, stop and say so instead of pushing anyway. Husky automates this at the git level
— see `git-policy.md` for exactly which of these run on commit vs on push.

## Lint & Format Standard

- **ESLint**: `@darraghor/eslint-plugin-nestjs-typed`'s flat recommended config (Nest-specific
  rules — e.g. every injectable's constructor params typed, DTO classes actually decorated with
  `class-validator`, controller methods returning the type their `@ApiResponse`/return type
  claims) layered on top of `typescript-eslint`'s `strict-type-checked` preset (full type-aware
  strictness: no floating promises, no unsafe `any` usage, exhaustive switch checks). Add
  `eslint-plugin-simple-import-sort` (or equivalent) and
  `@typescript-eslint/consistent-type-imports` so the group order in `code-style/imports.md` is
  machine-enforced, not just hand discipline. Add a restricted-import rule
  (`no-restricted-imports` / `eslint-plugin-boundaries`) so a module can't import another
  module's internals directly and `common`/`core` can't import "up" into `modules/` — see
  `architecture/module-boundaries.md`. Put `eslint-config-prettier` last in the config array so
  no ESLint stylistic rule fights Prettier's formatting.
- **Typed linting**: `strict-type-checked` needs `parserOptions.project` pointed at `tsconfig.json`
  for `src/**/*.ts`. Test files (`*.spec.ts`, `test/**/*.ts`) usually live under a separate
  `tsconfig` scope in a Nest project (or the same one, if `nest new` didn't split it) — verify
  which, and split the flat config into two blocks (typed for `src/`, non-typed for root-level
  `*.ts` config files like `eslint.config.js` itself and `jest.config.ts`) if they don't share
  one `tsconfig`.
- **Prettier**: config lives in `.prettierrc` at the project root (`singleQuote: true`,
  `printWidth: 100`, `trailingComma: "all"`). Don't hand-edit formatting rules anywhere else.
- **Editor consistency**: `.editorconfig` at the root pins indent size/style and final-newline
  behavior for any editor, independent of Prettier. `.vscode/extensions.json` recommends
  ESLint, Prettier, and the Prisma extension.
- **What each tool owns**: ESLint = correctness/type-safety, Prettier = whitespace/quotes/
  line-wrapping. Never add a formatting rule to ESLint config — that's Prettier's job and the
  two would fight.

## Ignoring files

- ESLint (`eslint.config.js` top-level `ignores` entry) and `.prettierignore` (a real file at
  the project root, kept in sync with the ESLint `ignores` list) both exclude: `dist/`,
  `node_modules/`, `coverage/`, `generated/` (Prisma client output — regenerated, never
  hand-formatted), lockfiles (`pnpm-lock.yaml`/`package-lock.json`/`yarn.lock`).
- `prisma/migrations/**/*.sql` is excluded from both — generated SQL, not hand-formatted code.
- `.agents/**/*.md` and `AGENTS.md`/`CLAUDE.md` are **not** excluded from Prettier — keep the
  docs formatted too.

## Non-English Content Check

The "English only, no Cyrillic/mojibake" rule (see `git-policy.md`, `AGENTS.md`) is backed by a
real check, not just eyeballing: add a `lint-staged` entry (or a standalone
`{{PACKAGE_MANAGER}} run check:i18n-leak` script) that greps staged text files for Cyrillic
characters specifically.

**Do not match "all non-ASCII"** (`[^\x00-\x7F]`) — that also flags legitimate typography this
project's own docs use on purpose (em dash `—`, en dash `–`, curly quotes, `→`, `×`,
non-breaking spaces). Match the actual Cyrillic Unicode block instead:

```sh
grep -PIrl '[\x{0400}-\x{04FF}]' -- "$@"
```

Wire it into the `pre-commit` Husky hook alongside `lint-staged` so it's non-optional. See
`git-policy.md`'s Husky Hooks section for the `sh -e` gotcha when wiring grep into a hook script.

## Writing tests

<!-- SCAFFOLD: keep only if unit tests were chosen -->
- Unit tests live next to the file under test (`thing.ts` + `thing.spec.ts`). Mock Prisma via a
  typed mock of `PrismaService`, not a real database connection.
<!-- SCAFFOLD: keep only if e2e tests were chosen -->
- E2E tests live under `test/` and use Supertest against a real (or Testcontainers-provisioned)
  Nest app instance — cover request/response contracts and auth flows, not implementation
  details.
<!-- SCAFFOLD: keep only if "both" (unit+e2e) was chosen, i.e. Testcontainers wired -->
- E2E tests run against a real Postgres started by `@testcontainers/postgresql` for the test
  run, migrated via `prisma migrate deploy` in a `beforeAll` — never against the dev database
  from `docker-compose.yml`, and never mocked.
- Test what the provider/controller is responsible for, not Nest internals (DI wiring itself
  doesn't need a test).
- Prefer testing observable behavior (returned DTOs, thrown exceptions, emitted events) over
  calling private methods directly.

## Review Checklist

- [ ] Lint, format check, and configured tests all pass before every push.
- [ ] New shared logic has at least one test covering its main behavior.
- [ ] No formatting rules added to ESLint config; no correctness rules disabled in Prettier.
- [ ] Lockfile never hand-formatted or ESLint/Prettier-touched.
- [ ] Generated Prisma client (`generated/`) and migration SQL never hand-edited.
