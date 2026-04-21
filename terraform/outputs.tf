output "bucket_name" {
  value = module.app_bucket.bucket_name
}

output "bucket_arn" {
  value = module.app_bucket.bucket_arn
}

output "bucket_url" {
  value = module.app_bucket.bucket_domain_name
}