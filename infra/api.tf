resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = 14
}

resource "aws_lambda_function" "api" {
  filename         = "${path.module}/../build/api.zip"
  function_name    = "${local.name_prefix}-api"
  role             = aws_iam_role.api.arn
  handler          = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../build/api.zip")

  runtime       = "python3.14"
  architectures = ["arm64"]

  memory_size = 128
  timeout     = 10

  environment {
    variables = {
      JOBS_TABLE     = aws_dynamodb_table.jobs.name
      JOBS_QUEUE_URL = aws_sqs_queue.jobs.url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.api,
    aws_iam_role_policy.api,
  ]
}

resource "aws_apigatewayv2_api" "jobs" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api" {
  api_id = aws_apigatewayv2_api.jobs.id

  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.api.invoke_arn

  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_job" {
  api_id = aws_apigatewayv2_api.jobs.id

  route_key = "POST /jobs"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_route" "get_job" {
  api_id = aws_apigatewayv2_api.jobs.id

  route_key = "GET /jobs/{job_id}"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id = aws_apigatewayv2_api.jobs.id

  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.jobs.execution_arn}/*/*"
}
