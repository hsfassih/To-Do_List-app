terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "hsfassih-todo-app"
    key            = "todo-app/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

module "app_bucket" {
  source = "./modules/s3_bucket"

  bucket_name        = var.bucket_name
  environment        = var.environment
  versioning_enabled = var.versioning_enabled

  tags = {
    Project = "todo-app"
  }
}

module "lambda" {
  source = "./modules/lambda"

  function_name    = "hello-lambda"
  s3_bucket        = var.bucket_name
  s3_key           = "lambda/function.zip"
  source_code_hash = var.lambda_source_hash
  environment      = var.environment
  timeout_seconds  = 10
}

module "lambda_getnewsfeed" {
  source = "./modules/lambda"

  function_name    = "getnewsfeed-lambda"
  s3_bucket        = var.bucket_name
  s3_key           = "lambda/getnewsfeed.zip"
  source_code_hash = var.getnewsfeed_source_hash
  environment      = var.environment
  handler          = "getnewsfeed.handler"
  timeout_seconds  = 30
  secret_arn       = "arn:aws:secretsmanager:us-east-1:957921932357:secret:todo-app/thenewsapi-token-y27FXL"
}

module "lambda_displaynews" {
  source = "./modules/lambda"

  function_name    = "displaynews-lambda"
  s3_bucket        = var.bucket_name
  s3_key           = "lambda/displaynews.zip"
  source_code_hash = var.displaynews_source_hash
  environment      = var.environment
  handler          = "displaynews.handler"
  timeout_seconds  = 15
  secret_arn       = "arn:aws:secretsmanager:us-east-1:957921932357:secret:todo-app/thenewsapi-token-y27FXL"
}

resource "aws_lambda_function_url" "displaynews" {
  function_name      = module.lambda_displaynews.function_name
  authorization_type = "NONE"
}

resource "aws_lambda_permission" "displaynews_function_url" {
  statement_id            = "AllowPublicFunctionUrlInvoke"
  action                  = "lambda:InvokeFunctionUrl"
  function_name           = module.lambda_displaynews.function_name
  principal               = "*"
  function_url_auth_type  = "NONE"
}

resource "aws_lambda_permission" "displaynews_invoked_via_url" {
  statement_id            = "AllowPublicInvokeViaFunctionUrl"
  action                  = "lambda:InvokeFunction"
  function_name           = module.lambda_displaynews.function_name
  principal               = "*"
  invoked_via_function_url = true
}