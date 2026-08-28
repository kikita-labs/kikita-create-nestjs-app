# Logging and Error Observability

`nestjs-pino` is the logging mechanism. It is not the application's error taxonomy. The code
that owns a failure decides whether it is expected, how it is rendered for the current transport,
and which bounded fields are safe to emit. Keep those decisions explicit and consistent.

## Fixed logging policy

- Use `nestjs-pino` for application and bootstrap logs. Use the structured logger API (`PinoLogger`
  or the project's typed wrapper) when adding fields. Do not rely on Nest `Logger`'s overloaded
  string signature to serialize arbitrary objects as structured data.
- Production logs are JSON on stdout. Development may use `pino-pretty` for readability, but the
  pretty transport is never the production format.
- Do not use `console.*` in application code. Enforce `no-console: 'error'` in ESLint. Configure
  the logger before application code starts emitting logs; do not add a console fallback merely
  because logger setup is inconvenient.
- Treat log fields as sensitive server-side data. Do not log passwords, access or refresh tokens,
  cookies, session identifiers, API keys, connection strings, nonces, raw request bodies, legal
  contents, payment data, or unnecessary personal data. Redact or allowlist values before they
  reach the logger.
- Configure `pinoHttp.redact` for authorization headers, cookies, `set-cookie`, and every
  project-specific secret path. Keep request bodies disabled unless a documented, field-level
  allowlist and security review justify an exception.
- Do not promise that a platform log viewer is an APM, error tracker, alerting system, or long-term
  retention store. Sentry, OpenTelemetry, Grafana/Loki, Datadog, and similar integrations are
  deployment decisions. Add one only when the project explicitly needs it and document the
  chosen integration.

## Error taxonomy

Every failure must belong to one of these categories before it is logged or rendered:

| Category | Examples | Response/log behavior |
| --- | --- | --- |
| Expected rejection | Validation, authentication, authorization, not found, conflict, rate limit, known domain rule | Return the safe transport response. Do not emit an `error` stack for normal client behavior. Let the access log or a bounded `debug`/`warn` event provide operational context when useful. |
| Expected dependency translation | A known Prisma, upstream API, or platform error with a defined mapping | Translate to a stable application error before the transport boundary. Never expose table names, columns, provider payloads, tokens, or raw upstream messages. |
| Unexpected application failure | Bug, invariant violation, unknown provider failure, malformed framework callback | Render a generic safe response or reply, and log it exactly once at the final transport/application boundary with the normalized fields below. |
| Process failure | Uncaught exception, unhandled rejection, or a failure outside a recoverable event boundary | Use the runtime/framework last-resort handler, record the failure, and let the process supervisor decide restart behavior. Do not silently continue after an unknown process failure. |

The logger does not make this classification automatically. Do not create a giant catch block that
turns every failure into the same event. Preserve the distinction between a normal 4xx outcome and
an unexpected 5xx failure.

## Structured error event

An unexpected error event has a stable, bounded shape. Use the project's names consistently:

```ts
{
  event: 'application_error',
  service: 'backend',
  operation: 'users.create',
  stage: 'persistence',
  errorCode: 'INTERNAL_ERROR',
  severity: 'error',
  requestId: 'validated-request-id',
  // traceId: 'only when OpenTelemetry is actually installed and active',
  error: {
    type: 'DatabaseError',
    // message and stacktrace are server-side fields only and must be sanitized
  },
}
```

- Every application-generated error or rejection event uses this common field set, including a
  low-severity event for an expected rejection. Routine expected 4xx outcomes may intentionally
  have no separate application event; the access log is sufficient. Do not treat that deliberate
  absence as permission to invent a second error shape.
- `operation` and `stage` use a documented, low-cardinality vocabulary. Do not put a URL with
  user input, a raw exception message, an ID, or a payload value in a field used for grouping.
- `errorCode` is a stable application code, not a database code, stack trace, or localized text.
  If another process consumes the error, define the code in the shared contract package rather
  than duplicating strings in each transport.
- `severity` describes the application event. The logger's own `level` remains the sink-level
  field; do not use arbitrary level names that the configured logger does not understand.
- Include `requestId` for HTTP and the transport's correlation ID for bot or WebSocket events.
  Include `traceId` only when a real tracing context exists. A request ID is not a fake trace ID.
- Prefer a normalized error type and an allowlisted safe summary. Never attach an entire caught
  exception as `{ exception }`, `{ error }`, or a stringified object unless a configured serializer
  has been verified to scrub secrets and unwanted fields. A stack trace is server-only diagnostic
  data, not a response field.

For expected errors, use the same stable `errorCode` and bounded `operation`/`stage` values in
metrics or low-severity events when they are operationally useful. Never use raw error messages,
user IDs, guild IDs, nonce values, or request payloads as metric labels.

## Catch and logging ownership

- Catch only when the code can recover, translate a known error, add safe context and rethrow, or
  render the final transport response. A catch that only logs and rethrows creates duplicate noise
  and often leaks the raw exception.
- Log an unexpected failure once at the boundary that owns the final outcome: an HTTP exception
  filter, a WebSocket/bot event boundary, a job failure boundary, or a last-resort process handler.
  Lower layers may add context to the error or translate it, but must not emit another error log.
- A request access log and one application error log are different events. Configure their levels
  deliberately; do not add a second stack log just because `pino-http` already recorded the
  request.
- Expected 4xx/domain rejections must not be logged as unexpected 5xx failures. If a rejection is
  security-relevant or repeated abuse is suspected, emit a bounded `warn` event without secrets.
- Keep the response/reply safe even when the server log contains diagnostic information. A generic
  public message plus `requestId` is preferable to returning `error.message` from an unknown error.

## Correlation by transport

### HTTP

Generate the request ID once at the HTTP boundary. Accept an inbound ID only after validating its
character set and length; otherwise generate a new ID. Echo the final value in `X-Request-Id` and
make the same value available to `pino-http` as `req.id` and to the exception filter.

Choose one owner for this logic. A middleware and `pinoHttp.genReqId` must share one helper or one
authoritative value; do not maintain two independent request-ID algorithms that can drift. Do not
trust an arbitrary inbound header as a trace or user identity.

### WebSocket, bot, and jobs

These transports do not automatically have an HTTP request ID. Create a short-lived correlation ID
at the event/job boundary and pass it through the handling flow. Use the platform's stable event or
job identifiers only when their privacy and cardinality are acceptable. Do not put user, guild,
chat, message, or payload data in log fields unless the project has explicitly approved and bounded
that field.

Use a transport-specific filter/handler for WebSocket or bot errors. An HTTP `APP_FILTER` does not
automatically define the error behavior of a platform callback. Map the error to the platform's
safe reply shape and apply the same classification, redaction, and one-boundary-log policy.

## Cross-process error contracts

The generated REST baseline keeps Nest's default `HttpException` response shape for a simple
single-transport application. That shape is not automatically a durable contract for another app.

When a web client, bot, worker, or another service consumes the response, define a documented
versioned envelope with at least a stable `errorCode`, safe localized `message`, optional
allowlisted `details`, and the correlation ID. Keep transport renderers separate: an HTTP JSON body,
a bot reply, and a WebSocket event need not have the same outer shape. Do not expose raw framework,
Prisma, upstream-provider, or exception metadata just to make the shapes match.

Known Prisma errors must be translated before the final HTTP renderer. The mapping belongs in the
global DI-managed `PrismaExceptionFilter` described by `architecture/transport-adapter.md`; it must
produce a safe application exception, not a raw database message or a generic unclassified 500.

## Optional tracing and external telemetry

Do not install a tracing or error-tracking vendor as a hidden substitute for logging. If the project
chooses OpenTelemetry, propagate its context, record exceptions in the active span/log pipeline,
and include the real `traceId` in correlated log events. Keep the same redaction rules: exception
messages, stack traces, attributes, and event payloads can contain sensitive data.

Alert thresholds, retention, dashboards, and browser error collection belong to the deployment or
client-observability documentation. They are not implied by `nestjs-pino` or by a Railway log viewer.

## Review Checklist

- [ ] Application code uses the configured structured logger; no `console.*` or plain Nest logger
      call is used for application events.
- [ ] Production output is JSON and development pretty output is not enabled in production.
- [ ] Authorization, cookies, `set-cookie`, and project-specific secrets are redacted; request
      bodies and raw payloads are not logged by default.
- [ ] Each catch is classified as recovery, translation, rethrow with context, or final rendering;
      no catch only logs and rethrows.
- [ ] Unexpected failures are logged once at the final boundary with bounded operation, stage,
      errorCode, severity, and the correct correlation ID.
- [ ] Expected 4xx/domain errors do not produce an error stack or raw exception dump.
- [ ] No whole exception, raw provider payload, token, nonce, personal data, or localized message
      is exposed in a response, log field, metric label, or telemetry attribute.
- [ ] HTTP request ID ownership is singular and the response header, logger, and filter use the
      same validated value; non-HTTP transports have an explicit correlation strategy.
- [ ] Cross-process consumers use a documented stable error contract rather than accidental Nest,
      Prisma, or provider output.
- [ ] Tests cover the applicable filter/handler behavior, redaction, correlation, and safe public
      rendering; metrics use bounded labels.
