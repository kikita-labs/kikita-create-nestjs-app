# Skill Installation Upgrade

Read this file before `update.md` when the user asks to update the skill itself, when the
installed skill predates the current Agent Skills layout, or when the skill is a copied/dirty
project-local directory.

There are three separate things to keep distinct:

1. **Canonical source** — a git clone of this repository. Its current skill is
   `skills/kikita-create-nestjs-app/SKILL.md`.
2. **Installed skill** — a symlink or Windows directory junction pointing at that subdirectory.
   The link must keep the canonical clone's `.git` reachable.
3. **Project documentation** — the target project's `AGENTS.md` and `.agents/` tree, updated by
   `update.md` after the installed skill is current.

Updating one layer does not automatically update the other two.

## Preflight

1. Resolve the directory containing the currently executing `SKILL.md`. Do not guess from a
   familiar home-directory path.
2. Run `git -C <resolved-skill-dir> rev-parse --show-toplevel`. A failure means the skill was
   copied without history or its link is broken. Do not attempt a template update from it.
3. Confirm the source clone has the current layout:

   ```text
   <repo-root>/skills/kikita-create-nestjs-app/SKILL.md
   <repo-root>/skills/kikita-create-nestjs-app/templates/
   ```

   A root-level `SKILL.md` plus root-level `templates/` is a legacy installation. The
   `plugin.json`/Agent Plugins layout is also not the current format.
4. Check `git -C <repo-root> status --porcelain`. Never pull over a dirty source clone. Report
   the files and preserve the local changes before replacing or relinking anything.
5. Select the source explicitly. For the latest published skill, use a clean clone updated from
   `origin/main`. If the user explicitly wants a local feature branch, report its commit and do
   not call it the latest published release.

## Migrating a legacy project-local installation

When the expected project-local path is a real legacy directory rather than a junction:

- Do not overwrite it in place.
- If it is dirty, preserve it as a dated backup before installing the new link. The backup is the
  legacy baseline and may contain user-authored skill changes; inspect and report those changes.
- If the user has not authorized replacing the path, stop after reporting the migration plan.
- Install the clean canonical clone in a persistent source directory and create a directory
  junction at `.claude/skills/kikita-create-nestjs-app` (or the client's equivalent) pointing to
  `<repo-root>/skills/kikita-create-nestjs-app`. Do not copy only the skill subdirectory; that
  drops the git history required by `update.md`.
- Restart the client only if it does not rescan changed skill links in the current session.

The first update after this migration may need two baselines: the preserved legacy template tree
and the current template tree. If the legacy commit exists in the canonical clone, use the normal
git diff. If it does not, compare the preserved legacy `templates/.agents/` tree with the current
`skills/kikita-create-nestjs-app/templates/.agents/` tree and merge the intent. A hash from an
unrelated or pruned repository is not a valid `git diff` baseline.

## Legacy scaffold records

Older projects may have this shape:

```json
{
  "skillCommit": "<git hash>",
  "scaffoldedAt": "<date>",
  "answers": { "...": "..." }
}
```

Treat `skillCommit` as the legacy spelling of `scaffoldedFromCommit`. Preserve `answers` and
unknown project metadata such as `monorepo`; do not re-ask the questionnaire. If both commit keys
exist and disagree, stop and report the conflict. After a successful update, write the current
canonical record shape with `scaffoldedFromCommit` and keep legacy provenance only if the project
needs it for audit.

If the legacy hash is not present in the current source clone, use the preserved legacy template
tree as described above. Do not report "no changes" merely because `git log <old-hash>..HEAD`
cannot resolve the old hash.

## Handoff to project update

Only after the skill source and installation pass this preflight, run `update.md` separately from
each target project directory. `update.md` updates `.agents/`; it does not scaffold a second app,
move source files, or silently repair application code. Keep source refactors, dependency changes,
and deployment changes outside this documentation migration unless the user separately requests
them.

## Review Checklist

- [ ] Canonical source is a clean git clone with the current `skills/.../SKILL.md` layout.
- [ ] The installed skill is a symlink/junction into that clone, not a copied directory.
- [ ] Any dirty legacy installation was preserved and its changes were reported.
- [ ] Legacy scaffold records with `skillCommit` were normalized without losing answers or
      project-specific metadata.
- [ ] An unreachable legacy hash was handled with the preserved template-tree fallback, not
      treated as a no-op.
- [ ] Project update mode was run separately for each target project only after this preflight.
