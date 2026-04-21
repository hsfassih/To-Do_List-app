variable "bucket_name" {
  description = "Globally unique name for the S3 bucket"
  type        = string
}

variable "environment" {
  description = "Deployment environment tag (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "versioning_enabled" {
  description = "Enable S3 versioning"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags to apply to the bucket"
  type        = map(string)
  default     = {}
}