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

  function_name    = "todo-app-lambda"
  s3_bucket        = var.bucket_name
  s3_key           = "lambda/function.zip"
  source_code_hash = var.lambda_source_hash
  environment      = var.environment
}