# Messaging (Message Broker)

Present only because this project opted into async messaging / inter-service events. Delete this
file (and its `architecture/README.md` link) if that questionnaire answer was "no".

## Scope: hybrid app, not separate microservices

This skill scaffolds **one** deployable Nest app. Choosing messaging does not split the project
into multiple services/repos (that's explicitly out of scope, same as a monorepo request — see
`SKILL.md`). Instead the single app also listens on the broker, via a hybrid setup in `main.ts`:

```ts
const app = await NestFactory.create(AppModule);
app.connectMicroservice<MicroserviceOptions>({
  transport: Transport.RMQ,
  options: {
    urls: [process.env.RABBITMQ_URL],
    queue: 'app_queue',
    queueOptions: { durable: true },
  },
});
await app.startAllMicroservices();
await app.listen(process.env.PORT ?? 3000);
```

## Default broker: RabbitMQ

RabbitMQ is the fixed default — task-queue semantics, flexible routing (direct/topic/fanout
exchanges), mature dead-letter-queue support, and it covers the overwhelming majority of
"notify another part of the system when X happens" / "process this job asynchronously" needs.

```ts
@Controller()
export class OrdersConsumer {
  constructor(private readonly ordersService: OrdersService) {}

  @EventPattern('order_created')
  async handleOrderCreated(@Payload() data: OrderCreatedEvent): Promise<void> {
    await this.ordersService.sendConfirmationEmail(data.orderId);
  }

  @MessagePattern('get_order_status')
  async getOrderStatus(@Payload() data: { orderId: string }): Promise<OrderStatus> {
    return this.ordersService.getStatus(data.orderId);
  }
}
```

`@EventPattern` = fire-and-forget (no reply expected). `@MessagePattern` = request/reply (the
handler's return value is published back). Use the one that matches the actual interaction —
don't `@MessagePattern` something that never needs a reply, it wastes a reply queue.

## When to consider Kafka instead

Not a scaffold-time choice — a later ADR-worthy migration if the project genuinely grows into
one of these (see `../decisions/README.md`):

- Event volume/throughput RabbitMQ can't comfortably sustain (Kafka handles orders of magnitude
  more messages/sec via partitioned, durable, ordered logs).
- Multiple independent consumers need to replay the same event stream from an arbitrary point
  (Kafka retains a log; RabbitMQ's queue delivers each message once and then it's gone).
- Multiple independent consumer groups each need their own full copy of every event (Kafka's
  consumer-group model does this natively; RabbitMQ needs a fanout exchange per group instead).

If none of these are true yet, stay on RabbitMQ — don't pre-optimize for a scale the project
hasn't reached.

## Review Checklist

- [ ] Broker connection wired via `app.connectMicroservice()` in the same app, not a second
      deployable service.
- [ ] `@EventPattern` used for fire-and-forget, `@MessagePattern` only where a reply is actually
      consumed.
- [ ] Queue/exchange names are constants (in `common/` or the owning module), not inline string
      literals repeated across producer and consumer.
- [ ] No Kafka introduced without an ADR justifying the migration trigger above.
