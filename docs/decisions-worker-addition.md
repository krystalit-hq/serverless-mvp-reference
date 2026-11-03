# Worker decisions — content to merge into docs/decisions.md

## Why an idempotency lease instead of a one-time lock?

SQS and Lambda provide at-least-once processing. Duplicate delivery is possible.

A permanent "seen this job_id" marker is not enough. If a worker claims a job
and crashes before completing it, a permanent lock can turn a retryable failure
into lost work.

The worker therefore creates a short processing lease. A retry can reclaim a
job after the lease expires. A completed job remains completed and duplicate
deliveries become harmless no-ops.

This is still a deliberately small reference pattern. Workloads with external
non-transactional side effects may require a stronger idempotency design.

## Why partial batch responses?

Without partial batch responses, one failed record causes successfully processed
records from the same SQS batch to become visible again.

The event source mapping enables `ReportBatchItemFailures`, and the worker
returns only the message IDs that should be retried.

## Why Python 3.14?

It is a current generally available AWS Lambda runtime on Amazon Linux 2023.
The reference deliberately avoids preview runtimes.

## Why ARM64?

The worker has no native dependencies and no architecture-specific requirement,
so ARM64 keeps the example small and cost-conscious without adding complexity.
