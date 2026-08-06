# Aliases & Barrels

## Path aliases

`tsconfig.json` `paths` maps `@app/*` to `src/*`. Any import crossing a module boundary
(`modules/users` importing something from `common/` or `core/`) uses the alias, never a relative
`../../../` climb:

```ts
// Good
import { PrismaService } from '@app/core/prisma/prisma.service';

// Bad
import { PrismaService } from '../../../core/prisma/prisma.service';
```

A relative import (`./`, `../`) is fine only for files inside the same module folder.

## Barrels

Nest modules already give a natural encapsulation boundary — a feature's `*.module.ts` declares
exactly what it exports via the `exports` array (see `module-boundaries.md`), so barrels here are
lighter-weight than in a frontend app: not every folder needs an `index.ts`.

- Add a barrel `index.ts` to a `modules/<feature>/` folder once it has more than the module/
  controller/service triplet (e.g. it grows a `dto/` folder with several DTOs another module is
  allowed to import — export the DTOs meant for reuse through the barrel, not the internals).
- `common/` and `core/` subfolders (`pipes/`, `filters/`, `core/queue/`, etc.) get a barrel as
  soon as they hold more than one file, since those are imported from many places across the app.
- Never barrel-export something not meant to be imported from outside the folder — a barrel is a
  public-surface declaration, not a convenience re-export of everything.

## Review Checklist

- [ ] No `../../../`-style deep relative imports crossing a module boundary — the alias was
      used instead.
- [ ] Every `common/`/`core/` subfolder with 2+ files has a barrel.
- [ ] Barrel exports match what's actually meant to be public — no accidental internal leak.
