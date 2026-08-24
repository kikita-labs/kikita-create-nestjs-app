# Testing & Quality Gate

This repo ships no executable code for end users — `SKILL.md`/`plan.md`/`templates/` are
instructions and template files, not a program. The gate here checks the *artifacts*, not
runtime behavior.

## Before every push

- No broken relative markdown links (a link target starting with `./` or `../` that
  doesn't resolve to a real file) anywhere in the repo.
- `skills/kikita-create-nestjs-app/SKILL.md`'s frontmatter is valid per the
  [Agent Skills spec](https://agentskills.io/specification): `name` matches the parent
  directory, `name`/`description` respect the length and character rules.
- English only in every tracked file — no stray Cyrillic or mojibake.

Run the same checks CI runs, locally, from the repo root:

```sh
python3 .github/scripts/check_links.py
grep -rInP '[\p{Cyrillic}]' --include=*.md --include=*.json .   # should print nothing
```

## CI

`.github/workflows/ci.yml` runs the same checks on every push and PR. Branch
protection on `main` requires this to pass before a PR can merge — don't merge over a
failing check, and don't disable the workflow to get around a real failure.

## Review Checklist

- [ ] All checks pass locally before pushing.
- [ ] CI is green before merging the PR.
