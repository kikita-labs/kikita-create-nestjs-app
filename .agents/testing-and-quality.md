# Testing & Quality Gate

This repo ships no executable code for end users — `SKILL.md`/`plan.md`/`templates/` are
instructions and template files, not a program. The gate here checks the *artifacts*, not
runtime behavior.

## Before every push

- No broken relative markdown links (a link target starting with `./` or `../` that
  doesn't resolve to a real file) anywhere in the repo.
- `plugin.json` is valid JSON and matches the Agent Plugins 1.0.0 manifest rules (`$schema`
  present and exact, `name` matches the pattern, only permitted top-level fields).
- English only in every tracked file — no stray Cyrillic or mojibake.

Run the same checks CI runs, locally, from the repo root:

```sh
python3 .github/scripts/check_links.py
python3 .github/scripts/check_plugin_json.py
grep -rInP '[\p{Cyrillic}]' --include=*.md --include=*.json .   # should print nothing
```

## CI

`.github/workflows/ci.yml` runs the same three checks on every push and PR. Branch
protection on `main` requires this to pass before a PR can merge — don't merge over a
failing check, and don't disable the workflow to get around a real failure.

## Review Checklist

- [ ] All three checks pass locally before pushing.
- [ ] CI is green before merging the PR.
