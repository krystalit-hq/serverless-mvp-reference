from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api_module(monkeypatch):
    monkeypatch.setenv("JOBS_TABLE", "test-jobs")
    monkeypatch.setenv("JOBS_QUEUE_URL", "https://example.invalid/jobs")

    import boto3

    table = MagicMock()
    dynamodb_resource = MagicMock()
    dynamodb_resource.Table.return_value = table
    sqs_client = MagicMock()

    original_resource = boto3.resource
    original_client = boto3.client

    def resource(service_name, *args, **kwargs):
        if service_name == "dynamodb":
            return dynamodb_resource
        return original_resource(service_name, *args, **kwargs)

    def client(service_name, *args, **kwargs):
        if service_name == "sqs":
            return sqs_client
        return original_client(service_name, *args, **kwargs)

    monkeypatch.setattr(boto3, "resource", resource)
    monkeypatch.setattr(boto3, "client", client)

    module = load_module(
        "serverless_mvp_api_handler",
        ROOT / "src" / "api" / "handler.py",
    )

    return module, table, sqs_client


@pytest.fixture
def worker_module(monkeypatch):
    monkeypatch.setenv("JOBS_TABLE", "test-jobs")
    monkeypatch.setenv("IDEMPOTENCY_LEASE_SECONDS", "30")

    import boto3

    table = MagicMock()
    dynamodb_resource = MagicMock()
    dynamodb_resource.Table.return_value = table

    original_resource = boto3.resource

    def resource(service_name, *args, **kwargs):
        if service_name == "dynamodb":
            return dynamodb_resource
        return original_resource(service_name, *args, **kwargs)

    monkeypatch.setattr(boto3, "resource", resource)

    module = load_module(
        "serverless_mvp_worker_handler",
        ROOT / "src" / "worker" / "handler.py",
    )

    return module, table
