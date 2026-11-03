import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError


JOBS_TABLE = os.environ["JOBS_TABLE"]
LEASE_SECONDS = int(os.environ.get("IDEMPOTENCY_LEASE_SECONDS", "30"))

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(JOBS_TABLE)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log(level: str, message: str, **fields: Any) -> None:
    payload = {
        "level": level.upper(),
        "message": message,
        **fields,
    }
    getattr(logger, level.lower())(json.dumps(payload, separators=(",", ":")))


def parse_message(record: dict[str, Any]) -> dict[str, Any]:
    body = json.loads(record["body"])

    job_id = body.get("job_id")
    correlation_id = body.get("correlation_id")

    if not job_id or not correlation_id:
        raise ValueError("message must contain job_id and correlation_id")

    return {
        "job_id": job_id,
        "correlation_id": correlation_id,
        "payload": body.get("payload", {}),
    }


def claim_job(job_id: str, correlation_id: str) -> str:
    now = int(time.time())
    lease_expires_at = now + LEASE_SECONDS

    try:
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=(
                "SET #status = :processing, "
                "correlation_id = :correlation_id, "
                "processing_started_at = :now, "
                "processing_expires_at = :lease_expires_at, "
                "updated_at = :now"
            ),
            ConditionExpression=(
                "attribute_not_exists(#status) "
                "OR #status = :queued "
                "OR (#status = :processing AND processing_expires_at < :now)"
            ),
            ExpressionAttributeNames={
                "#status": "status",
            },
            ExpressionAttributeValues={
                ":queued": "QUEUED",
                ":processing": "PROCESSING",
                ":correlation_id": correlation_id,
                ":now": now,
                ":lease_expires_at": lease_expires_at,
            },
        )
        return "claimed"

    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise

    existing = table.get_item(
        Key={"job_id": job_id},
        ConsistentRead=True,
    ).get("Item")

    if existing and existing.get("status") == "COMPLETED":
        return "completed"

    return "busy"


def perform_work(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("force_failure") is True:
        raise RuntimeError("forced failure requested by payload")

    return {
        "accepted_payload": payload,
        "processed": True,
    }


def complete_job(
    job_id: str,
    correlation_id: str,
    result: dict[str, Any],
) -> None:
    now = int(time.time())

    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=(
            "SET #status = :completed, "
            "#result = :result, "
            "completed_at = :now, "
            "updated_at = :now "
            "REMOVE processing_expires_at"
        ),
        ConditionExpression=(
            "#status = :processing AND correlation_id = :correlation_id"
        ),
        ExpressionAttributeNames={
            "#status": "status",
            "#result": "result",
        },
        ExpressionAttributeValues={
            ":processing": "PROCESSING",
            ":completed": "COMPLETED",
            ":correlation_id": correlation_id,
            ":result": result,
            ":now": now,
        },
    )


def process_record(record: dict[str, Any]) -> None:
    message_id = record["messageId"]
    message = parse_message(record)

    job_id = message["job_id"]
    correlation_id = message["correlation_id"]

    claim = claim_job(job_id, correlation_id)

    if claim == "completed":
        log(
            "info",
            "duplicate_job_ignored",
            message_id=message_id,
            job_id=job_id,
            correlation_id=correlation_id,
        )
        return

    if claim == "busy":
        raise RuntimeError(
            f"job {job_id} is already being processed by an active lease"
        )

    log(
        "info",
        "job_processing_started",
        message_id=message_id,
        job_id=job_id,
        correlation_id=correlation_id,
    )

    result = perform_work(message["payload"])
    complete_job(job_id, correlation_id, result)

    log(
        "info",
        "job_processed",
        message_id=message_id,
        job_id=job_id,
        correlation_id=correlation_id,
    )


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    failures = []

    for record in event.get("Records", []):
        try:
            process_record(record)
        except Exception:
            message_id = record.get("messageId", "unknown")

            log(
                "exception",
                "job_processing_failed",
                message_id=message_id,
            )

            failures.append({
                "itemIdentifier": message_id,
            })

    return {
        "batchItemFailures": failures,
    }
