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

variable "lambda_source_hash" {
  description = "Base64-encoded SHA256 hash of the Lambda zip - injected by CI"
  type = string
  default = ""
}

variable "getnewsfeed_source_hash" {
  description = "Base64-encoded SHA256 of the getnewsfeed Lambda zip"
  type        = string
  default     = ""
}

variable "displaynews_source_hash" {
  description = "Base64-encoded SHA256 of the displaynews Lambda zip"
  type        = string
  default     = ""
}