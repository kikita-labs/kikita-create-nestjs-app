# How to Write and Maintain Documentation

This is the master file. Read it before creating or editing anything under `.agents/`.

## Structure

- `AGENTS.md` at the repo root is the hub: a short "Must Read" list plus non-negotiable
  rules. It never contains detailed explanations — those live in `.agents/`.
- A topic that fits in one short file stays a flat `.agents/<topic>.md`.
- A topic that has grown, or is expected to grow, into several related documents gets its
  own subfolder (`.agents/code-style/`, `.agents/architecture/`, `.agents/shared/`,
  `.agents/core/`, `.agents/decisions/`). Every such subfolder has a `README.md` that:
  - briefly states what the subfolder covers,
  - links to every other file in the subfolder,
  - gives short, general instructions on how to extend the subfolder correctly.
- Never create a new subfolder for a single file. Two or more genuinely distinct documents
  is the minimum bar.

## Style

- Imperative, short sentences. No filler, no marketing language.
- Every rule should be checkable — prefer "Blank line before `return`." over "Try to keep
  code readable."
- Back non-obvious rules with a short code example.
- End every doc with a short "Review Checklist" of the concrete things to verify.
- English only. No Cyrillic, no mojibake, anywhere in tracked files.

## Mandatory updates

Documentation is not optional maintenance — it's part of the change, not a follow-up. The
change and its doc update land in the same commit, not a "docs: catch up" commit later.

Concretely, before you consider a change done, ask: did I just —

- Add, remove, or change a **reusable piece** (generic pipe, filter, interceptor, decorator, or
  framework-agnostic utility) under `src/common/`? → update `.agents/shared/README.md` (table
  row) and, if it has a real API surface, its own `.agents/shared/<name>.md`.
- Add, remove, or change an **app-wide singleton** — service, guard, provider — under
  `src/core/`? → update `.agents/core/README.md` (table row) and, if non-trivial, its own
  `.agents/core/<name>.md`.
- Add, remove, or change a **Prisma model or field**? → the migration is part of the change
  (see `workflow.md`); if the change affects the DTO reuse pattern or a shared validation rule,
  update `.agents/code-style/dto-and-validation.md` too.
- Change a **convention** the user asked for or corrected you on — import order, folder
  layout, alias scheme, member ordering, anything under `.agents/code-style/` or
  `.agents/architecture/` — even a small tweak? → update the matching file immediately,
  don't wait for it to come up again. The doc is what makes the correction stick for next
  time instead of getting re-litigated.
- Change feature placement or decomposition — for example, move a domain feature out of
  `core/`, split an over-flat feature into named capabilities, or add a recognized file suffix —
  → update `architecture/folder-structure.md` and `code-style/module-structure.md` together.
- Add a new role (client, builder, state store, registry) or split a grab-bag constants/utility
  file? → document the responsibility-first classification rule and its allowed scope before
  adding another role folder.
- Create, change, move, or delete a source file? → run `.agents/file-change-review.md` for that
  file. Update this documentation set too if the change introduces a new placement, decomposition,
  testing, or comment convention.
- Still unsure whether a change needs a doc update? It probably does — check the relevant
  README before skipping it.

## Review Checklist

- [ ] New doc placed flat or in a subfolder per the rule above, not arbitrarily.
- [ ] Subfolder `README.md` updated to link the new file, if applicable.
- [ ] Doc ends with a Review Checklist.
- [ ] English only, no leftover `{{PLACEHOLDER}}` tokens.
