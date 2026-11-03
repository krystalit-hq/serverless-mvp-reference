# API decisions — content to merge into docs/decisions.md

## Why HTTP API instead of REST API?

The reference only needs two simple Lambda proxy routes. HTTP API keeps the
surface smaller and avoids features the example does not currently need.

## Why payload format 2.0?

The API is built specifically for HTTP API and does not need REST API
compatibility. Payload format 2.0 gives the current HTTP API event shape.

## Why write QUEUED before sending to SQS?

A client that receives a job ID should be able to query that job immediately.
The API creates the job record first and then publishes the message.

There is no distributed transaction between DynamoDB and SQS. If enqueueing
fails, the API compensates by marking the record as SUBMISSION_FAILED.

A stronger guarantee would require a different coordination pattern and is
deliberately outside this reference.

## Why no authentication yet?

Authentication is not needed to demonstrate the architecture's core concerns:
asynchronous processing, retry, idempotency, traceability and responsibility
boundaries. A real public deployment should make an explicit authentication
and authorization decision.

## Why no CORS configuration?

The reference does not assume a browser client. CORS should be added when an
actual browser origin exists rather than enabled speculatively.
