# Architecture decisions

## Why SQS?

The HTTP request lifecycle should not own the lifecycle of background work.
SQS creates a simple asynchronous boundary and gives the worker retry semantics
without introducing an orchestration engine.

## Why a DLQ?

Retry without a terminal place for persistent failures only postpones the
problem. Failed messages must become inspectable rather than disappear into an
infinite retry loop.

## Why DynamoDB?

The reference needs a small job/status store keyed by `job_id`. The data model
does not require joins or relational constraints, so a relational database
would add more operational surface than value.

## Why PAY_PER_REQUEST?

This is an MVP reference with unknown and likely low initial traffic.
On-demand capacity removes capacity planning from the first iteration.

## Why no Terraform modules?

The current infrastructure is intentionally small and has no stable
responsibility boundaries that justify modules. Files group resources by
concern without hiding the dependency graph behind premature abstractions.

## Why no Step Functions?

One queue and one worker do not yet form a workflow complex enough to justify
an orchestration service.

## Why no prescribed remote Terraform backend?

State storage is tied to ownership, environment and delivery process.
Hard-coding a shared backend into a reference project would hide that decision
rather than explain it.
