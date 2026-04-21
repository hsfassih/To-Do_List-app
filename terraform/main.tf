terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
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