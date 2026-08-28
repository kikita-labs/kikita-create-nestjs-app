# File Change Review

Run this gate after creating, changing, moving, or substantially deleting every source file.
Source files include TypeScript/JavaScript, DTOs, providers, modules, tests, configuration, and
database schema files. Documentation changes use `documentation.md`'s checklist instead.

For a change touching several files, run the file gate for each file, then run the module-level
checks in `architecture/folder-structure.md`, `code-style/module-structure.md`, and
`testing-and-quality.md`. Do not report the change as complete while a blocking item is open.

## 1. Classify ownership before writing code

Write a short inventory before creating a new file or moving an existing one:

| Question | Answer to record |
| --- | --- |
| What business capability owns the behavior? | A feature such as `legal`, `users`, or `billing` |
| What role does the file play? | Controller, provider, client, builder, store, guard, type, or constant |
| Who consumes it? | One file, one capability, the feature, or multiple features |
| What is its visibility? | Private implementation, feature API, or app-wide infrastructure |
| What is the smallest vertical slice that keeps it and its tests together? | The target path |

Use the inventory to choose the path. Do not choose a path because a folder already exists or
because every file has the same prefix.

- Put business/domain behavior in `src/modules/<feature>/`. `src/core/` is for app-wide technical
  singletons and infrastructure wrappers. `@Global()` changes DI visibility; it does not change
  ownership.
- Keep a small feature root for its module, primary transport/service, and feature-wide files.
  Once it reaches six production `.ts` files or contains two distinct capabilities, split it into
  named capability folders. Do not create generic `services/`, `controllers/`, `utils/`, `types/`,
  or `misc/` buckets.
- Keep related workflow files together even when their suffixes differ. A builder, update handler,
  guard, client, and state store for one acceptance flow may belong in one `acceptance/` slice.
  Create `builders/`, `clients/`, `guards/`, or `state/` only for multiple related files or a real
  subsystem boundary.
- Move a source file and its `.spec.ts` together. Update exact imports and the owning module's
  `controllers`, `providers`, and `exports` arrays in the same change.

### Declarations, entities, and constants

Inspect every declaration in the file before accepting its location:

- A reusable `interface`, `type`, `enum`, or exported `const` belongs in the matching scoped
  `interfaces/`, `enums/`, or `constants/` folder. A one-off type used by one function may stay
  inline. A private map or helper type used only by one utility may stay private.
- A DTO describes a transport contract. A Prisma model/generated type describes persistence. Do
  not create a domain entity only to fill an `entities/` folder or copy a database model into a
  controller response.
- Create a `*.entity.ts` domain entity only when it owns domain invariants or behavior. Put it in
  the owning feature/capability's `entities/` folder when there is more than one related entity or
  the entity is a clear domain boundary; a single small entity may stay beside the capability.
- Keep one constant file per cohesive family. Split action, error, metrics, modal, and lifecycle
  constants when their consumers or reasons to change differ. A large `<feature>.constants.ts`
  grab bag is a decomposition failure, not a reason to keep adding sections.
- A `*.util.ts` file contains focused helper functions and private implementation details. It does
  not contain providers, interfaces used elsewhere, or unrelated constants. Put an error helper in
  an `errors/` capability, not in a generic `utilities/` bucket.

## 2. Check responsibility and decomposition

Before adding a new method or declaration, ask whether the file still has one primary reason to
change. Split by business capability or workflow, not by arbitrary line count and not by familiar
technical role names alone.

Use these size signals for hand-written source. They are maintainability gates, not a license to
pad a file with comments or to split three-line files into meaningless fragments:

| Signal | Required action |
| --- | --- |
| File over 300 non-blank, non-comment lines | Review the responsibility split before adding more code |
| File over 400 non-blank, non-comment lines | Split before merge, unless a documented generated/vendor/data-only exception is approved |
| Function or method over 40 non-blank, non-comment lines | Look for an extraction or a clearer branch structure |
| Function or method over 80 non-blank, non-comment lines | Extract a cohesive operation by default; record why it stays whole if not |
| Function or method over 120 non-blank, non-comment lines | Blocking: split it before merge, except generated/vendor code |

A 200-line function is not an acceptable default. Extract parsing, validation, persistence, mapping,
side effects, and error handling into named operations with one responsibility each. A long class
made of many small methods can still be over-scoped; split it when its methods serve different
capabilities or change for different reasons. Do not hide a large method behind section comments.

The generated ESLint config must enforce the 400-line file and 120-line function caps with
`max-lines` and `max-lines-per-function`; see `testing-and-quality.md`. Also enable complexity and
nesting checks there. Treat lint suppressions as exceptions requiring a reason and approval, not as
the normal way to keep an oversized file.

## 3. Decide the test at the same time

Do not postpone the test decision until after the implementation exists:

| Changed file | Test expectation |
| --- | --- |
| Service, provider, guard, interceptor, filter, client, builder, store, registry, or non-trivial utility | Add or update a focused unit test for observable behavior |
| Controller or bot update handler | Cover the transport contract with e2e/integration tests when configured; otherwise add a unit test when it has meaningful branching |
| DTO with custom/nested validation or transformation | Test rejection/acceptance of the important invalid and valid shapes |
| Module with non-trivial conditional wiring or public exports | Add a metadata/integration test; a trivial `@Module()` wrapper does not need a ceremonial spec |
| Interface, type, enum, or constants-only file | No standalone test; test the behavior of the consumer |
| Refactor or file move | Keep existing tests unchanged where behavior is unchanged, and run them after every structural slice |

Place unit specs next to the source file. Keep e2e tests under `test/`. Prefer observable behavior
over calls to private methods. A new runtime file without a test is an explicit decision, not an
accident; record the reason in the change summary when the matrix says a test is expected.

## 4. Review comments and public surface

- Keep comments that explain why, an invariant, a security constraint, a compatibility workaround,
  or a non-obvious algorithm. Remove comments that merely narrate the next line of code.
- Delete or update stale comments in the same change. A comment must describe current behavior, not
  a planned refactor.
- When mandatory TSDoc was selected, follow `agent-surface.md` for every public export. Otherwise,
  still document public contracts and non-obvious invariants; do not add TSDoc to every private line
  by habit.
- Comments and TSDoc are English-only. Do not use comments to justify an architecture that the
  folder/module rules reject.

## 5. Finish the gate

After the file passes the review above:

1. Check imports, module registration, and public exports. Look for a circular dependency created
   by the new path.
2. Run the relevant unit/e2e tests, type-check, lint, and format check. Run the full configured
   gate before commit.
3. If a generated/vendor/data-only file must exceed a threshold, exclude only that path from the
   mechanical rule and record the reason. Never add a blanket disable for application code.
4. If the change alters a folder convention, module boundary, or recognized file type, update the
   matching `.agents/` documentation in the same change.

## Review Checklist

- [ ] Ownership, role, consumers, visibility, and target path were recorded before writing the file.
- [ ] The file is in the correct feature/capability folder; no folder was chosen from a prefix or
      from an existing role-folder list.
- [ ] Reusable declarations, entities, constants, and utility details are in the correct scope.
- [ ] The file has one primary responsibility and passes the size/decomposition signals above.
- [ ] A 200-line function, grab-bag constants file, or unrelated inline declaration was not left
      behind.
- [ ] The test expectation was decided and the required spec/e2e coverage exists or its exception
      is documented.
- [ ] Comments explain why/invariants and match current behavior; no narration or stale comments.
- [ ] Specs moved with source, imports/module arrays/exports are correct, and no cycle was added.
- [ ] Relevant tests, type-check, lint, and format checks pass.
