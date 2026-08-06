# Architecture

How the project is laid out and wired together.

- [folder-structure.md](./folder-structure.md) — top-level project layout.
- [aliases-and-barrels.md](./aliases-and-barrels.md) — path aliases (`@app/*`, `@generated/*`)
  and why this project never uses barrel `index.ts` files.
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
  `eslint-plugin-boundaries`) blocking a module from importing another module's genuinely
  private subfolders, and — specifically — any `@nestjs/*` import inside
  `src/common/utilities/**`. This is cheap to set up at scaffold time and catches violations
  before review.

  Since this project never uses barrel files (`aliases-and-barrels.md`), a legitimate
  cross-module import is always a direct file path one level into another module
  (`@app/modules/notes/notes.service`, `@app/modules/notes/dto/create-note.dto`,
  `@app/modules/notes/entities/note.entity`) — a path-depth-based glob like
  `@app/modules/*/*` would block those too, along with the actually-private internals it's meant
  to catch. Target the specific subfolders `folder-structure.md`'s file-type table marks
  feature-private instead (`interfaces/`, `enums/`, `constants/`, `guards/` — never `dto/`,
  `entities/`, or a module's own top-level files, which are the legitimate public surface):

  ```js
  {
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          {
            group: [
              '@app/modules/*/interfaces/*',
              '@app/modules/*/enums/*',
              '@app/modules/*/constants/*',
              '@app/modules/*/guards/*',
            ],
            message: 'This subfolder is feature-private — see architecture/folder-structure.md.',
          },
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
