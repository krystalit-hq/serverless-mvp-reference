variable "aws_region" {
  description = "AWS region used by the reference stack."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Base name used for AWS resources."
  type        = string
  default     = "serverless-mvp-reference"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, numbers and hyphens."
  }
}

variable "sqs_visibility_timeout_seconds" {
  description = "How long a received message stays invisible while the worker processes it."
  type        = number
  default     = 60

  validation {
    condition     = var.sqs_visibility_timeout_seconds >= 1
    error_message = "sqs_visibility_timeout_seconds must be at least 1."
  }
}

variable "sqs_max_receive_count" {
  description = "Number of receives before SQS moves a message to the DLQ."
  type        = number
  default     = 3

  validation {
    condition     = var.sqs_max_receive_count >= 1
    error_message = "sqs_max_receive_count must be at least 1."
  }
}
