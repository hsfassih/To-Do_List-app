variable "function_name"    { type = string }
variable "s3_bucket"        { type = string }
variable "s3_key"           { type = string; default = "lambda/function.zip" }
variable "source_code_hash" { type = string; default = "" }
variable "environment"      { type = string; default = "dev" }
variable "runtime"          { type = string; default = "python3.12" }
variable "handler"          { type = string; default = "function1.handler" }