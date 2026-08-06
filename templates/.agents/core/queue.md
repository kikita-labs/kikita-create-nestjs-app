# Queue (Background Jobs)

Present only because this project opted into background jobs. Delete this file (and its
`core/README.md` row / `AGENTS.md` bullet) if that questionnaire answer was "no".

`@nestjs/bullmq` + `bullmq` against the Redis instance from `docker-compose.yml` (`REDIS_URL`).
Use this for anything that shouldn't block the request/event that triggered it: sending an
email, generating a report, calling a slow third-party API.

```ts
// core/queue/queue.module.ts
@Module({
  imports: [
    BullModule.forRootAsync({
      useFactory: () => ({ connection: { url: process.env.REDIS_URL } }),
    }),
  ],
  exports: [BullModule],
})
export class QueueModule {}
```

```ts
// modules/notifications/notifications.processor.ts
@Processor('notifications')
export class NotificationsProcessor extends WorkerHost {
  async process(job: Job<SendEmailJobData>): Promise<void> {
    await this.mailer.send(job.data);
  }
}
```

## Conventions

- One `BullModule.registerQueue({ name: '<queue>' })` per logical queue, registered in the
  owning feature module (`modules/notifications/`), not centralized in `core/queue/` — `core/`
  only wires the shared Redis connection.
- Job payloads are typed interfaces, not `any` — define `<Job>Data` next to the processor.
- Always set `attempts` + a backoff strategy when adding a job (`removeOnComplete`/
  `removeOnFail` too) — an unbounded-retry or never-cleaned queue silently grows Redis memory.
- Failed jobs after all retries go to a dead-letter path (a separate queue or a logged alert),
  not silently dropped.

## Review Checklist

- [ ] Queue registered in its owning feature module, not in `core/`.
- [ ] Job data has a typed interface.
- [ ] `attempts`/backoff/`removeOnComplete`/`removeOnFail` set explicitly, not left at BullMQ
      defaults without a documented reason.
- [ ] Exhausted-retry jobs are handled (DLQ or alert), not silently dropped.
