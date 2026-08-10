# Agent Surface (TSDoc)

Present only because this project opted into mandatory TSDoc. Delete this file (and its
`AGENTS.md` link) if that questionnaire answer was "no".

- Every exported provider, controller, DTO class (and its fields), guard, interceptor, and type
  has a TSDoc comment: one line stating what it is, plus `@param`/`@returns` when not obvious
  from the signature.
- DTO fields document the *business* constraint, not the decorator that already says it —
  `@IsEmail()` already tells the reader it's an email; the comment should say what it's used for
  if that's not obvious from the field name.
- TSDoc is English only, same as all other tracked content.
- Do not document behavior that isn't implemented yet — TSDoc describes what the code does now,
  not the roadmap.
- Keep TSDoc next to the declaration it documents; don't centralize it in a separate file.

```ts
/** Formats a user's display name, falling back to their email local-part. */
export function formatDisplayName(user: User): string {
  return user.displayName ?? user.email.split('@')[0];
}

export class CreateUserDto {
  /** Must be unique across all users; used as the login identifier. */
  @IsEmail()
  email!: string;
}
```

## Review Checklist

- [ ] Every new public export has TSDoc.
- [ ] TSDoc matches current behavior, not planned behavior.
- [ ] English only.
