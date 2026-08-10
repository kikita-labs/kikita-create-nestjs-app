# .agents

Documentation index. `AGENTS.md` at the repo root tells an agent what's mandatory to read for a
given task; this file is the flat map of everything that exists under `.agents/`.

## Root docs

- [workflow.md](./workflow.md) — task sequence to follow.
- [git-policy.md](./git-policy.md) — commit/push rules and authority.
- [documentation.md](./documentation.md) — how to write and maintain these docs.
- [testing-and-quality.md](./testing-and-quality.md) — lint/format/test gate.
- [refactoring.md](./refactoring.md) — refactor policy.
- [progress.md](./progress.md) — dated status log.
<!-- SCAFFOLD: keep only if mandatory TSDoc was chosen -->
- [agent-surface.md](./agent-surface.md) — TSDoc requirements.

## Subfolders

- [code-style/](./code-style/README.md) — formatting, imports, provider structure, DTO/
  validation conventions, module structure.
- [architecture/](./architecture/README.md) — folder layout, aliases, module boundaries,
  transport adapter (REST/bot), messaging.
- [shared/](./shared/README.md) — registry of `src/common/` (framework-agnostic utilities and
  generic pipes/filters/interceptors/guards/middleware/decorators/exceptions/interfaces/enums/
  constants).
- [core/](./core/README.md) — registry of `src/core/` app-wide singletons (Prisma client, config
  schema, logger, health checks, auth, queue, cache, storage, i18n).
- [decisions/](./decisions/README.md) — ADRs for hard-to-reverse architectural changes.

Read `documentation.md` before adding, moving, or restructuring anything here. It's the master
rulebook for *when* a doc update is mandatory — e.g. a new reusable utility/provider/interceptor
goes in `shared/` or `core/`, and a user-corrected convention goes in `code-style/` or
`architecture/` — right away, not as a follow-up.
