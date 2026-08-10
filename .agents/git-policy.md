# Git Policy

- Commit messages: concise, English, imperative mood ("Add gated queue template block", not
  "Added"/"Adding").
- **Never** add `Co-authored-by`, `Claude-Session`, `Generated-by`, or any other AI/assistant
  attribution line to a commit message — in this repo or any other repo touched while
  working here. Hard rule, no exceptions, no "just this once."
- Never claim co-authorship for Claude, Codex, ChatGPT, or any other AI tool.
- One feature/fix/doc change per branch, named `<type>/<short-description>`
  (`feat/`, `fix/`, `docs/`).
- `main` is branch-protected: PR required, direct pushes and force-pushes rejected for
  everyone including the repo owner. If a push to `main` is ever rejected for this reason,
  open a PR — don't try to bypass protection.
- Before staging broadly (`git add .`/`git add -A`), review `git status` — don't stage
  anything you haven't looked at.
- Before any command that could discard uncommitted work (`checkout`/`restore`/`reset`/
  `clean`), run `git status` first and stash or commit anything found.
- Delete merged branches, both local and `origin` — don't let stale branches pile up.

## Review Checklist

- [ ] No AI attribution anywhere in the commit message.
- [ ] Change is on its own branch, merged via PR, not pushed directly to `main`.
- [ ] Merged branch deleted (local + `origin`) after merge.
