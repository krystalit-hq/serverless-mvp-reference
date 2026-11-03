output "api_endpoint" {
  description = "Base URL of the HTTP API."
  value       = aws_apigatewayv2_api.jobs.api_endpoint
}

output "api_function_name" {
  description = "Name of the API Lambda function."
  value       = aws_lambda_function.api.function_name
}

output "api_log_group_name" {
  description = "CloudWatch Logs group used by the API Lambda."
  value       = aws_cloudwatch_log_group.api.name
}
