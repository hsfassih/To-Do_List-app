output "bucket_name" {
  value = module.app_bucket.bucket_name
}

output "bucket_arn" {
  value = module.app_bucket.bucket_arn
}

output "bucket_url" {
  value = module.app_bucket.bucket_domain_name
}

output "lambda_function_name" {
  value = module.lambda.function_name
}

output "lambda_function_arn" {
  value = module.lambda.function_arn
}

output "getnewsfeed_function_name" {
  value = module.lambda_getnewsfeed.function_name
}

output "displaynews_function_name" {
  value = module.lambda_displaynews.function_name
}

output "displaynews_function_url" {
  value = aws_lambda_function_url.displaynews.function_url
}