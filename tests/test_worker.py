import json

from botocore.exceptions import ClientError


def sqs_record(
    message_id="message-1",
    job_id="job-1",
    correlation_id="corr-1",
    payload=None,
):
    return {
        "messageId": message_id,
        "body": json.dumps(
            {
                "job_id": job_id,
                "correlation_id": correlation_id,
                "payload": payload or {},
            }
        ),
    }


def conditional_failure():
    return ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "condition failed",
            }
        },
        "UpdateItem",
    )


def test_successful_record_is_completed(worker_module, monkeypatch):
    worker, table = worker_module

    monkeypatch.setattr(worker.time, "time", lambda: 1_700_000_000)
    worker.process_record(sqs_record(payload={"hello": "world"}))

    assert table.update_item.call_count == 2
    claim = table.update_item.call_args_list[0].kwargs
    assert claim["ExpressionAttributeValues"][":queued"] == "QUEUED"

    complete = table.update_item.call_args_list[1].kwargs
    assert complete["ExpressionAttributeValues"][":completed"] == "COMPLETED"


def test_completed_duplicate_is_ignored(worker_module):
    worker, table = worker_module

    table.update_item.side_effect = conditional_failure()
    table.get_item.return_value = {
        "Item": {"job_id": "job-1", "status": "COMPLETED"}
    }

    worker.process_record(sqs_record())

    assert table.update_item.call_count == 1
    table.get_item.assert_called_once()


def test_forced_failure_is_reported_as_partial_batch_failure(worker_module):
    worker, _ = worker_module

    result = worker.lambda_handler(
        {
            "Records": [
                sqs_record(
                    message_id="failed-message",
                    payload={"force_failure": True},
                )
            ]
        },
        None,
    )

    assert result == {
        "batchItemFailures": [{"itemIdentifier": "failed-message"}]
    }


def test_malformed_message_is_reported_as_failure(worker_module):
    worker, _ = worker_module

    result = worker.lambda_handler(
        {
            "Records": [
                {"messageId": "bad-json", "body": "{not-json}"}
            ]
        },
        None,
    )

    assert result == {
        "batchItemFailures": [{"itemIdentifier": "bad-json"}]
    }


def test_active_processing_lease_is_not_stolen(worker_module):
    worker, table = worker_module

    table.update_item.side_effect = conditional_failure()
    table.get_item.return_value = {
        "Item": {"job_id": "job-1", "status": "PROCESSING"}
    }

    try:
        worker.process_record(sqs_record())
    except RuntimeError as exc:
        assert "already being processed" in str(exc)
    else:
        raise AssertionError("expected active lease rejection")
