output "bucket_name" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "The bucket domain name (URL)"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_region" {
  description = "The AWS region where the bucket was created"
  value       = aws_s3_bucket.this.region
}