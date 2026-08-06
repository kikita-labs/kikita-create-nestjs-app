# Storage (File Uploads)

Present only because this project opted into file uploads. Delete this file (and its
`core/README.md` row / `AGENTS.md` bullet) if that questionnaire answer was "no".

One storage-adapter interface, two implementations selected by `STORAGE_DRIVER` env var — the
vendor is never a scaffold-time or code-time choice, only a deploy-time one.

```ts
// core/storage/storage.interface.ts
export interface StorageAdapter {
  upload(key: string, body: Buffer, contentType: string): Promise<void>;
  getUrl(key: string): Promise<string>;
  delete(key: string): Promise<void>;
}
```

- `LocalStorageAdapter` (`STORAGE_DRIVER=local`) — writes under `STORAGE_LOCAL_PATH`, for local
  dev only.
- `S3StorageAdapter` (`STORAGE_DRIVER=s3`) — talks to any S3-compatible endpoint
  (`STORAGE_S3_ENDPOINT`): AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces all speak the same
  protocol, so the adapter code never changes, only the env vars.

```ts
// core/storage/storage.module.ts
@Module({
  providers: [
    {
      provide: STORAGE_ADAPTER,
      useFactory: () =>
        process.env.STORAGE_DRIVER === 's3' ? new S3StorageAdapter() : new LocalStorageAdapter(),
    },
  ],
  exports: [STORAGE_ADAPTER],
})
export class StorageModule {}
```

## Upload handling

```ts
@Post('avatar')
@UseInterceptors(FileInterceptor('file', { storage: multer.memoryStorage() }))
async uploadAvatar(
  @UploadedFile(new FileValidationPipe({ maxSizeBytes: 5 * 1024 * 1024, allowedMimeTypes: ['image/png', 'image/jpeg'] }))
  file: Express.Multer.File,
): Promise<{ url: string }> {
  const key = `avatars/${randomUUID()}`;
  await this.storage.upload(key, file.buffer, file.mimetype);
  return { url: await this.storage.getUrl(key) };
}
```

- **Always `multer.memoryStorage()`**, never `diskStorage()` — no temp file ever touches the
  container's disk; the buffer streams straight to the storage adapter.
- **`limits`** (`fileSize`, `files`) enforced at the Multer interceptor level, not just checked
  after the fact — rejects an oversized upload before it's fully buffered.
- **MIME-type whitelist** enforced in a custom pipe (`FileValidationPipe` above), checking the
  actual file content/magic bytes if the library supports it — never trust the client-supplied
  `Content-Type` header alone.

## Review Checklist

- [ ] `StorageAdapter` interface has exactly one call site choosing the implementation (the
      module factory), never an `if (env === 's3')` scattered through feature code.
- [ ] Multer always uses `memoryStorage()`, never `diskStorage()`.
- [ ] `limits` and a MIME-type whitelist enforced on every upload endpoint.
- [ ] Storage vendor never hardcoded — only `STORAGE_DRIVER`/`STORAGE_S3_*` env vars change it.
