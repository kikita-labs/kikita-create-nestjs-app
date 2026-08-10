# Imports

Group imports in this order, with a blank line between groups (no blank line within a group):

1. Node builtins (`node:fs`, `node:path`, ...).
2. `@nestjs/*` packages.
3. Third-party packages (`prisma`/`@prisma/client`, `zod`, `class-validator`, platform libraries
   like `telegraf`/`discord.js`, ...).
4. Project path-alias imports (`@app/...`, `@generated/...`, see
   `../architecture/aliases-and-barrels.md`).
5. Local relative imports (same module, `./`).
6. Type-only imports last within whichever group they belong to (`import type { ... }`).

```ts
import { randomUUID } from 'node:crypto';

import { Injectable, NotFoundException } from '@nestjs/common';

import { z } from 'zod';

import { PrismaService } from '@app/core/prisma/prisma.service';

import { UsersService } from './users.service';
import type { CreateUserDto } from './dto/create-user.dto';
```

- Never deep-import past a module's public surface (`@app/modules/orders/internal/foo`) — import
  what the module exports instead. See `../architecture/module-boundaries.md`. A module's public
  surface is its `*.module.ts` `exports` array, not a barrel — see
  `../architecture/aliases-and-barrels.md` for why this project never uses `index.ts` re-export
  files.
- This order isn't just hand-formatting discipline — `eslint-plugin-simple-import-sort` plus
  `@typescript-eslint/consistent-type-imports` enforce it at lint time. See
  `../testing-and-quality.md` for the exact `groups` array — **`simple-import-sort/imports: 'error'`
  with no `groups` option set does not enforce this order**, it falls back to the plugin's own
  default (roughly: side-effect imports, then everything else sorted alphabetically as one block),
  which sorts `@app/...` before `@nestjs/...` and produces lint-clean code that still violates
  every rule on this page. The custom `groups` array is not optional wiring.

## Review Checklist

- [ ] Groups in the order above, blank line between groups.
- [ ] No deep imports past a module's declared public surface.
- [ ] No barrel (`index.ts`) import anywhere — every import names the exact declaring file.
- [ ] `eslint.config.js`'s `simple-import-sort/imports` rule has the explicit `groups` array from
      `../testing-and-quality.md`, not just the plugin enabled with defaults — confirm by checking
      the config, not by assuming the plugin's presence is enough.
