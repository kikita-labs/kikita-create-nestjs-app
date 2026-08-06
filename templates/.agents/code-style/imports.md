# Imports

Group imports in this order, with a blank line between groups (no blank line within a group):

1. Node builtins (`node:fs`, `node:path`, ...).
2. `@nestjs/*` packages.
3. Third-party packages (`prisma`/`@prisma/client`, `zod`, `class-validator`, platform libraries
   like `telegraf`/`discord.js`, ...).
4. Project path-alias imports (`@app/...`, see `../architecture/aliases-and-barrels.md`).
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
  what the module exports instead. See `../architecture/module-boundaries.md`.
- A barrel (`index.ts`, where one exists) exports only symbols meant for outside consumers. No
  `export *` — list exports explicitly so accidental surface growth is visible in review.
- Type-only exports from a barrel use `export type { Foo }`, not a plain `export { Foo }`.
- This order isn't just hand-formatting discipline — `eslint-plugin-simple-import-sort` (or
  equivalent) plus `@typescript-eslint/consistent-type-imports` enforce it at lint time. See
  `../testing-and-quality.md`.

## Review Checklist

- [ ] Groups in the order above, blank line between groups.
- [ ] No deep imports past a module's declared public surface.
- [ ] Barrel exports are explicit, not `export *`; type-only exports use `export type`.
