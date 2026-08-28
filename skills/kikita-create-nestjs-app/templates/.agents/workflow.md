# Workflow

Follow this sequence for any task in this repo.

1. Read `AGENTS.md`, then the `.agents/*.md` files it points to that are relevant to the task.
2. Run `git status` before touching anything — know what's already dirty before you start.
3. Check `.agents/shared/README.md` and `.agents/core/README.md` before building a new utility,
   provider, or singleton — reuse before you build.
4. Check `prisma/schema.prisma` before adding a field or model that might already exist.
5. Before creating, changing, or moving a source file, read `.agents/file-change-review.md` and
   write its ownership/consumer/path inventory. Run that gate after each file; do not defer it to
   the end of a multi-file change.
6. Write the code following `.agents/code-style/` and `.agents/architecture/`.
7. If a Prisma schema change was made, run the migration (`npx prisma migrate dev --name
   <description>`) and commit the generated migration file alongside the schema change — never
   hand-edit a migration after it's been applied.
8. Update the matching `.agents/` doc in the same change if you added, removed, or changed a
   shared utility, core singleton, DTO convention, or module boundary. If the change was
   substantial (a milestone, not routine work), update `.agents/progress.md` too.
9. Run lint, format check, and tests (whichever are configured) before committing. See
   `.agents/testing-and-quality.md`.
10. Before committing, run `git diff --check` and scan the diff for Cyrillic or mojibake —
   tracked content must be English only. This is also enforced mechanically: see
   `.agents/testing-and-quality.md`'s "Non-English Content Check".
11. Commit following `.agents/git-policy.md`.

## Review Checklist

- [ ] Read the relevant docs before writing code, not after.
- [ ] Ran `file-change-review.md` after every source-file create/change/move; no blocking size or
      decomposition signal remains.
- [ ] No shared/reusable code introduced without a doc entry.
- [ ] Schema changes have a matching, committed Prisma migration.
- [ ] Lint, format, and tests (if configured) pass locally before commit.
- [ ] Commit message follows `.agents/git-policy.md`.
