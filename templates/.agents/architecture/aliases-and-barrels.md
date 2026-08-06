# Path Aliases

No barrel files (`index.ts` re-export hubs) anywhere in this project — see "No barrels" below
for why. Every import names the exact file the symbol comes from.

## `@app/*`

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

## `@generated/*`

Prisma's generated client (`prisma/schema.prisma`'s `generator client { output = "../generated/
prisma" }`, per `core/README.md`'s Prisma entry) lives at `<repo root>/generated/`, **outside**
`src/` — `@app/*` doesn't reach it, since that alias only covers `src/*`. Without a second alias,
every file that imports the generated client (`PrismaService`, any file importing a Prisma-
generated enum) ends up with a `../../../generated/prisma/client`-style path whose depth changes
every time the importing file moves. Add a second `tsconfig.json` `paths` entry:

```json
{
  "compilerOptions": {
    "paths": {
      "@app/*": ["src/*"],
      "@generated/*": ["generated/*"]
    }
  }
}
```

```ts
// Good
import { PrismaClient } from '@generated/prisma/client';
import { Role } from '@generated/prisma/enums';

// Bad
import { PrismaClient } from '../../../generated/prisma/client';
```

`tsc-alias` (see `plan.md`'s tooling step) and every Jest `moduleNameMapper` need this second
mapping alongside `@app/*` — the same subsystem, one more entry, not a separate one to remember.

## No barrels

Never create an `index.ts` that only re-exports other files in the same folder, and never import
through one. Two separate, both real, reasons — not just a style preference:

- **NestJS's own docs call this out as a circular-dependency trap specifically for imports within
  the same directory as the barrel**: a file inside `modules/users/` importing another file in
  that same folder through `modules/users/index.ts` (instead of the direct relative path) creates
  a dependency cycle through the barrel that isn't obvious from either file's own contents. Nest's
  circular-dependency docs name this exact pattern as a common, easy-to-miss cause.
- **Barrels defeat tree-shaking and slow down tooling that isn't bundler-aware**: TypeScript does
  not tree-shake a barrel import at compile time, so importing one named export from an `index.ts`
  can pull in every module that barrel re-exports (transitively, including their own imports).
  Jest in particular resolves and evaluates the whole barrel chain to satisfy one import — an
  otherwise-fast, narrowly-scoped test file can end up loading half the app's dependency graph.

Nest modules already give a real encapsulation boundary without needing a barrel for it — a
feature's `*.module.ts` declares exactly what it exports via the `exports` array (see
`module-boundaries.md`). That's the project's actual public-surface mechanism; an `index.ts`
re-export was never required for it to work.

```ts
// Good — direct import from the declaring file
import { UsersService } from '@app/modules/users/users.service';

// Bad — even if modules/users/index.ts only re-exports "public" things, this is a barrel import
import { UsersService } from '@app/modules/users';
```

## Review Checklist

- [ ] No `../../../`-style deep relative imports crossing a module boundary — `@app/*` or
      `@generated/*` used instead.
- [ ] No `index.ts` barrel file anywhere under `src/` — every import names the exact declaring
      file.
- [ ] `@generated/*` present in `tsconfig.json` `paths`, `tsc-alias`, and every Jest
      `moduleNameMapper` alongside `@app/*`.
