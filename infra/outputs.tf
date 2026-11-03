output "jobs_queue_url" {
  description = "URL of the SQS work queue."
  value       = aws_sqs_queue.jobs.url
}

output "jobs_queue_arn" {
  description = "ARN of the SQS work queue."
  value       = aws_sqs_queue.jobs.arn
}

output "jobs_dlq_url" {
  description = "URL of the dead-letter queue."
  value       = aws_sqs_queue.jobs_dlq.url
}

output "jobs_dlq_arn" {
  description = "ARN of the dead-letter queue."
  value       = aws_sqs_queue.jobs_dlq.arn
}

output "jobs_table_name" {
  description = "Name of the DynamoDB jobs table."
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  description = "ARN of the DynamoDB jobs table."
  value       = aws_dynamodb_table.jobs.arn
}

output "worker_function_name" {
  description = "Name of the Lambda worker."
  value       = aws_lambda_function.worker.function_name
}

output "worker_log_group_name" {
  description = "CloudWatch Logs group used by the worker."
  value       = aws_cloudwatch_log_group.worker.name
}
