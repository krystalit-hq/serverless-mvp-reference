data "aws_iam_policy_document" "api_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRole",
    ]

    principals {
      type = "Service"

      identifiers = [
        "lambda.amazonaws.com",
      ]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${local.name_prefix}-api"
  assume_role_policy = data.aws_iam_policy_document.api_assume_role.json
}

data "aws_iam_policy_document" "api" {
  statement {
    sid    = "SendJobs"
    effect = "Allow"

    actions = [
      "sqs:SendMessage",
    ]

    resources = [
      aws_sqs_queue.jobs.arn,
    ]
  }

  statement {
    sid    = "ReadAndCreateJobs"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.jobs.arn,
    ]
  }

  statement {
    sid    = "WriteApiLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "${aws_cloudwatch_log_group.api.arn}:*",
    ]
  }
}

resource "aws_iam_role_policy" "api" {
  name   = "${local.name_prefix}-api"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api.json
}
