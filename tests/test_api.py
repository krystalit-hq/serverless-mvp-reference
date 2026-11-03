import json
from decimal import Decimal


def post_event(body: str, correlation_id: str = "corr-test"):
    return {
        "routeKey": "POST /jobs",
        "headers": {"x-correlation-id": correlation_id},
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {"requestId": "gateway-request-id"},
    }


def get_event(job_id: str):
    return {
        "routeKey": "GET /jobs/{job_id}",
        "headers": {},
        "pathParameters": {"job_id": job_id},
        "requestContext": {"requestId": "get-request-id"},
    }


def test_post_job_returns_202_and_enqueues(api_module, monkeypatch):
    api, table, sqs = api_module

    monkeypatch.setattr(api.uuid, "uuid4", lambda: "job-123")
    monkeypatch.setattr(api.time, "time", lambda: 1_700_000_000)

    result = api.lambda_handler(post_event('{"hello":"world"}'), None)

    assert result["statusCode"] == 202
    body = json.loads(result["body"])
    assert body["job_id"] == "job-123"
    assert body["status"] == "QUEUED"

    written = table.put_item.call_args.kwargs["Item"]
    assert written["correlation_id"] == "corr-test"

    message = json.loads(sqs.send_message.call_args.kwargs["MessageBody"])
    assert message["payload"] == {"hello": "world"}


def test_post_job_rejects_invalid_json(api_module):
    api, table, sqs = api_module

    result = api.lambda_handler(post_event("{not-json}"), None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["error"] == "invalid_json"
    table.put_item.assert_not_called()
    sqs.send_message.assert_not_called()


def test_enqueue_failure_marks_submission_failed(api_module, monkeypatch):
    api, table, sqs = api_module

    monkeypatch.setattr(api.uuid, "uuid4", lambda: "job-123")
    monkeypatch.setattr(api.time, "time", lambda: 1_700_000_000)
    sqs.send_message.side_effect = RuntimeError("queue unavailable")

    result = api.lambda_handler(post_event('{"hello":"world"}'), None)

    assert result["statusCode"] == 503
    values = table.update_item.call_args.kwargs["ExpressionAttributeValues"]
    assert values[":failed"] == "SUBMISSION_FAILED"


def test_get_job_returns_public_completed_state(api_module):
    api, table, _ = api_module

    table.get_item.return_value = {
        "Item": {
            "job_id": "job-123",
            "status": "COMPLETED",
            "correlation_id": "corr-123",
            "completed_at": Decimal("1700000001"),
            "result": {"processed": True},
            "internal_field": "must-not-leak",
        }
    }

    result = api.lambda_handler(get_event("job-123"), None)
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["completed_at"] == 1_700_000_001
    assert body["result"]["processed"] is True
    assert "internal_field" not in body


def test_get_missing_job_returns_404(api_module):
    api, table, _ = api_module
    table.get_item.return_value = {}

    result = api.lambda_handler(get_event("missing"), None)

    assert result["statusCode"] == 404
