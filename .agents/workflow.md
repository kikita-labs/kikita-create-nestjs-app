# Workflow

Follow this sequence for any change to this repo.

1. Read `AGENTS.md`, then the `.agents/*.md` files it points to.
2. `git checkout -b <type>/<short-description>` off `main` — never commit directly on
   `main`, it's branch-protected and will reject the push anyway. See `git-policy.md`.
3. Make the change in the right place:
   - Skill behavior/instructions (questionnaire, mode detection, generation rules) →
     `skills/kikita-create-nestjs-app/SKILL.md`, `plan.md`, `adopt.md`, `update.md`,
     `upgrade.md`, `checklist.md`.
   - What gets generated into a user's project → `skills/kikita-create-nestjs-app/templates/`.
     See `documentation.md` for placeholder/gate rules before editing here.
   - Install instructions, repo structure, or what the skill does at a glance → root
     `README.md`.
   - Skill metadata → `SKILL.md`'s frontmatter (`metadata.version`). See `versioning.md` for
     when it must bump.
4. Run the checks in `testing-and-quality.md` locally before pushing.
5. Commit following `git-policy.md`.
6. Push the branch and open a PR into `main`. CI must be green before merging.
7. If `SKILL.md`'s `metadata.version` was bumped in this change: after the PR merges, tag
   and release it immediately, same sitting — see `versioning.md`. A version bump without a
   matching tag/release is not done yet.

## Review Checklist

- [ ] Change made on a feature branch, not directly on `main`.
- [ ] Correct file touched — skill logic vs template vs `SKILL.md` frontmatter vs README
      (step 3).
- [ ] No leftover `{{PLACEHOLDER}}` or broken relative link introduced (checked by CI, but
      verify before pushing).
- [ ] `metadata.version` in `SKILL.md` bumped if `versioning.md`'s rule says so.
- [ ] If `version` was bumped: tag pushed and GitHub release created after merge (see
      `versioning.md`) — not deferred, not skipped.
- [ ] Commit message has no AI-attribution line.
