import base64
import json
import logging
import os
import time
import uuid
from decimal import Decimal
from typing import Any

import boto3

JOBS_TABLE = os.environ["JOBS_TABLE"]
JOBS_QUEUE_URL = os.environ["JOBS_QUEUE_URL"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(JOBS_TABLE)
sqs = boto3.client("sqs")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log(level: str, message: str, **fields: Any) -> None:
    payload = {"level": level.upper(), "message": message, **fields}
    getattr(logger, level.lower())(json.dumps(payload, separators=(",", ":")))


def json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


def response(status_code: int, body: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
    headers = {"content-type": "application/json"}
    if correlation_id:
        headers["x-correlation-id"] = correlation_id

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(json_safe(body), separators=(",", ":")),
    }


def correlation_id_from(event: dict[str, Any]) -> str:
    headers = {str(k).lower(): v for k, v in (event.get("headers") or {}).items()}
    provided = headers.get("x-correlation-id")
    if provided:
        return provided[:128]

    return event.get("requestContext", {}).get("requestId") or str(uuid.uuid4())


def parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body")
    if raw is None:
        return {}

    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")

    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")

    return body


def create_job(event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    try:
        payload = parse_json_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return response(
            400,
            {
                "error": "invalid_json",
                "message": "Request body must be a valid JSON object.",
            },
            correlation_id,
        )

    job_id = str(uuid.uuid4())
    now = int(time.time())

    table.put_item(
        Item={
            "job_id": job_id,
            "status": "QUEUED",
            "correlation_id": correlation_id,
            "created_at": now,
            "updated_at": now,
        },
        ConditionExpression="attribute_not_exists(job_id)",
    )

    message = {
        "job_id": job_id,
        "correlation_id": correlation_id,
        "payload": payload,
    }

    try:
        sqs.send_message(
            QueueUrl=JOBS_QUEUE_URL,
            MessageBody=json.dumps(message, separators=(",", ":")),
        )
    except Exception:
        failed_at = int(time.time())
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=(
                "SET #status = :failed, updated_at = :updated_at, last_error = :last_error"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":failed": "SUBMISSION_FAILED",
                ":updated_at": failed_at,
                ":last_error": "failed_to_enqueue",
            },
        )

        log(
            "exception",
            "job_enqueue_failed",
            job_id=job_id,
            correlation_id=correlation_id,
        )

        return response(
            503,
            {"error": "queue_unavailable", "job_id": job_id},
            correlation_id,
        )

    log(
        "info",
        "job_accepted",
        job_id=job_id,
        correlation_id=correlation_id,
    )

    return response(
        202,
        {
            "job_id": job_id,
            "status": "QUEUED",
            "correlation_id": correlation_id,
        },
        correlation_id,
    )


def get_job(event: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    job_id = (event.get("pathParameters") or {}).get("job_id")

    if not job_id:
        return response(400, {"error": "missing_job_id"}, correlation_id)

    item = table.get_item(
        Key={"job_id": job_id},
        ConsistentRead=True,
    ).get("Item")

    if not item:
        return response(
            404,
            {"error": "job_not_found", "job_id": job_id},
            correlation_id,
        )

    public_fields = {
        key: item[key]
        for key in (
            "job_id",
            "status",
            "correlation_id",
            "created_at",
            "processing_started_at",
            "completed_at",
            "updated_at",
            "result",
            "last_error",
        )
        if key in item
    }

    return response(200, public_fields, correlation_id)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    correlation_id = correlation_id_from(event)
    route_key = event.get("routeKey")

    if route_key == "POST /jobs":
        return create_job(event, correlation_id)

    if route_key == "GET /jobs/{job_id}":
        return get_job(event, correlation_id)

    return response(404, {"error": "route_not_found"}, correlation_id)
