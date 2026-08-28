# Refactoring Policy

- Refactor in small, behavior-preserving slices. Each slice should be independently
  reviewable and independently revertable.
- Never mix a structural refactor with an unrelated feature change or visual tweak in the
  same commit.
- Before a refactor, confirm the current behavior (read the tests, or the code, closely
  enough to state it in one sentence). After, confirm nothing changed except what you
  intended.
- If a refactor touches a shared utility or a core singleton, update its doc entry in
  `.agents/shared/README.md` / `.agents/core/README.md` in the same change — see
  `.agents/documentation.md`.
- Prefer extracting over rewriting: pull duplicated logic into a helper rather than
  reimplementing both call sites.

## Feature-layout refactors

When a feature is over-flat or sits under the wrong top-level boundary, classify its files before
moving them. Write an old-path → new-path map grouped by capability, role, consumers, and public
visibility. Move production files and their specs together, then update exact imports and the
owning module's `controllers`/`providers`/`exports` arrays. Do not split a single workflow into
`services/`, `builders/`, `clients/`, or `utils/` folders merely because those names exist; keep
the workflow together and add role subfolders only when they express a real subsystem.

For a business feature incorrectly placed under `src/core/`, move it to
`src/modules/<feature>/` even if its module is singleton-scoped or currently marked `@Global()`;
remove `@Global()` by default and add explicit module imports. `@Global()` is a DI visibility
choice, not a reason to change domain ownership. If retaining it is unavoidable, record the reason
in an ADR. Run the feature's tests, the affected module tests, type-check, and lint after each
structural slice.

## Review Checklist

- [ ] Each commit is either "refactor" or "behavior change", never both.
- [ ] Tests (if configured) still pass after the refactor with no changes to their
      assertions, unless the refactor intentionally changed behavior.
- [ ] Docs updated if a shared piece moved or changed shape.
