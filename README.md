# Serverless MVP Reference

A small AWS reference architecture for building asynchronous MVP workloads
without pretending failure does not exist.

The goal is not to demonstrate how many AWS services can fit into one diagram.

It is to show the minimum architecture needed to answer a few important
questions early:

- What happens when processing fails?
- What happens when the same message is delivered twice?
- How do we trace one request across asynchronous boundaries?
- Where does failed work go?
- What can each component actually access?

**Production-aware does not mean production-complete.**

## Status

Work in progress.

The first infrastructure slice contains:

- Amazon SQS work queue
- Dead-letter queue
- Explicit redrive policy
- Amazon DynamoDB jobs table
- Terraform configuration with shared tagging

Next: worker Lambda, idempotent processing, API Lambda and HTTP API.

## Intended architecture

```text
API Gateway
    |
    v
Lambda API
    |
    v
   SQS --------> DLQ
    |
    v
Lambda Worker
    |
    v
DynamoDB
```

## Principles

- Failure paths are part of the architecture.
- Retry does not replace idempotency.
- Async boundaries should remain traceable.
- Permissions should follow responsibility boundaries.
- Abstractions are added when the system earns them.

## Terraform

```bash
make init
make fmt
make validate
make plan
```

By default the example uses `eu-central-1` and the `dev` environment.

Override values with CLI variables or your own untracked `terraform.tfvars`.

## State

This repository intentionally does not prescribe a shared Terraform backend.

A state backend is an ownership and environment decision. The reference keeps
that decision outside the example instead of pretending that one backend
configuration fits every consumer.

## Deliberately not included

- Cognito
- Step Functions
- EventBridge
- ECS / EKS
- Redis
- RDS
- WAF
- a custom observability platform
- Terraform modules without a real responsibility boundary

See `docs/decisions.md` for the reasoning behind the architecture.
