variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name for the S3 bucket"
  type        = string
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "versioning_enabled" {
  type    = bool
  default = false
}