# Architecture decisions

The point is not to present these choices as universal best practices. The
point is to make the trade-offs visible.

## Why HTTP API instead of REST API?

The reference only needs two simple Lambda proxy routes. HTTP API keeps the
surface smaller.

## Why payload format 2.0?

The application is built specifically for API Gateway HTTP API and does not
need REST API compatibility.

## Why SQS?

The HTTP request lifecycle should not own the lifecycle of background work.

SQS creates a simple asynchronous boundary and retry semantics without an
orchestration engine.

## Why a DLQ?

Retry without a terminal place for persistent failures only postpones the
problem. Failed work must become inspectable.

## Why `maxReceiveCount = 5`?

A transient failure should have several opportunities to recover before work
is dead-lettered. The value is explicit because failure policy is architecture.

## Why DynamoDB?

The model is small:

```text
job_id → status + timestamps + result
```

It does not need joins or relational constraints.

## Why PAY_PER_REQUEST?

An MVP has unknown and usually low initial traffic. On-demand capacity removes
capacity planning from the first iteration.

## Why write `QUEUED` before publishing to SQS?

A client that receives a job ID should be able to query it immediately.

There is no distributed transaction between DynamoDB and SQS. If enqueueing
fails, the API compensates with:

```text
SUBMISSION_FAILED
```

A stronger guarantee would require another coordination pattern.

## Why an idempotency lease?

A permanent "seen this job ID" marker can lose work if the worker crashes after
claiming the job but before completing it.

A short processing lease can expire, allowing a retry to reclaim the work.

A `COMPLETED` job stays terminal, so later duplicate deliveries become harmless
no-ops.

## Why partial batch responses?

One failed record should not force already successful records from the same SQS
batch to be retried.

The mapping enables:

```text
ReportBatchItemFailures
```

## Why structured logs without a larger observability stack?

JSON logs plus a correlation ID are enough to answer the questions this
reference is designed to answer. Another platform would add more surface than
signal.

## Why separate IAM roles?

The API and worker have different responsibilities. The roles reflect those
boundaries.

## Why no Terraform modules?

The infrastructure is intentionally small and does not yet have stable
responsibility boundaries that justify modules.

## Why no Step Functions?

One queue and one worker do not form a workflow complex enough to justify an
orchestration engine.

## Why no authentication?

Identity matters in a real public system, but it is outside the core problem
demonstrated here. A real deployment should make an explicit auth decision.

## Why no CORS configuration?

The reference does not assume a browser client. Configure CORS when an actual
browser origin exists.

## Why no prescribed remote Terraform backend?

Terraform state belongs to an ownership and delivery model. A reference repo
cannot know the consumer's correct backend or environment boundary.

## Why does a DLQ message not automatically become `FAILED` in DynamoDB?

SQS owns transport state. The application owns business state.

A production system that requires synchronized terminal failure could add a DLQ
consumer, reconciliation, or a workflow system with stronger state semantics.

The reference leaves that boundary visible instead of hiding it behind another
component.
