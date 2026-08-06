# Architecture

How the project is laid out and wired together.

- [folder-structure.md](./folder-structure.md) — top-level project layout.
- [aliases-and-barrels.md](./aliases-and-barrels.md) — path aliases, barrel `index.ts` rules.
- [module-boundaries.md](./module-boundaries.md) — how modules expose a public surface and how
  cross-module imports are restricted.
- [transport-adapter.md](./transport-adapter.md) — REST/bot transport layer, where it ends and
  shared business logic begins.
<!-- SCAFFOLD: keep only if messaging was chosen -->
- [messaging.md](./messaging.md) — hybrid message-broker transport (RabbitMQ/Kafka).

Adding a new architecture doc: only for a genuinely new structural concern. Link it here
immediately.

If the user changes or corrects a structural convention (folder layout, module boundaries,
transport pattern), update the matching file above in the same change — don't wait for it to
come up again. See `../documentation.md`.

Changing the transport strategy, messaging topology, or versioning scheme itself (not just
documenting it) needs an ADR — see `../decisions/README.md`.

## Automated boundary checks

Two layers, don't rely on discipline alone:

- **From day one**: an ESLint restricted-import rule (`no-restricted-imports` or
  `eslint-plugin-boundaries`) blocking a module from importing another module's internals
  directly, and — specifically — any `@nestjs/*` import inside `src/common/utilities/**`. This is
  cheap to set up at scaffold time and catches violations before review. Shape, using
  `no-restricted-imports`'s `patterns` option:

  ```js
  {
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          { group: ['@app/modules/*/*'], message: 'Import from a module\'s public surface (its module/service exports), not its internals.' },
          { group: ['@nestjs/*'], message: 'common/utilities must stay framework-agnostic.' } // scoped to src/common/utilities/** files only
        ],
      }],
    },
  }
  ```

- **Once the project grows**: a small custom boundary-check script plus `madge --circular` wired
  into CI, for boundary logic too nuanced for a single ESLint rule. Not required for a fresh
  project — worth doing once the import graph is complex enough that review alone stops catching
  violations.
