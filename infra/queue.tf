resource "aws_sqs_queue" "jobs_dlq" {
  name                      = "${local.name_prefix}-jobs-dlq"
  message_retention_seconds = 1209600

  sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue" "jobs" {
  name                       = "${local.name_prefix}-jobs"
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20

  sqs_managed_sse_enabled = true
}

resource "aws_sqs_queue_redrive_policy" "jobs" {
  queue_url = aws_sqs_queue.jobs.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })
}

resource "aws_sqs_queue_redrive_allow_policy" "jobs_dlq" {
  queue_url = aws_sqs_queue.jobs_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.jobs.arn]
  })
}
