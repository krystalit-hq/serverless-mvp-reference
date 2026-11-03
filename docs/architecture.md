# Architecture

## Request path

Planned:

```text
POST /jobs
    |
    v
API Gateway
    |
    v
Lambda API
    |
    v
SQS work queue
    |
    v
Lambda Worker
    |
    v
DynamoDB
```

## Failure path

```text
SQS work queue
    |
    | retry
    v
Lambda Worker
    |
    | after max receive count
    v
DLQ
```

The failure path is intentionally visible. A successful request path alone is
not enough to describe the system.
