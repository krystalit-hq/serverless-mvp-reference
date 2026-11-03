resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${local.name_prefix}-worker"
  retention_in_days = 14
}

resource "aws_lambda_function" "worker" {
  filename         = "${path.module}/../build/worker.zip"
  function_name    = "${local.name_prefix}-worker"
  role             = aws_iam_role.worker.arn
  handler          = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../build/worker.zip")

  runtime       = "python3.14"
  architectures = ["arm64"]

  memory_size = 128
  timeout     = 10

  environment {
    variables = {
      JOBS_TABLE                = aws_dynamodb_table.jobs.name
      IDEMPOTENCY_LEASE_SECONDS = "30"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.worker,
    aws_iam_role_policy.worker,
  ]
}

resource "aws_lambda_event_source_mapping" "jobs" {
  event_source_arn = aws_sqs_queue.jobs.arn
  function_name    = aws_lambda_function.worker.arn

  batch_size = 5
  enabled    = true

  function_response_types = [
    "ReportBatchItemFailures",
  ]
}
