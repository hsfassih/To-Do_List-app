resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
  tags = { Project = "todo-app", ManagedBy = "terraform" }
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_read" {
  name = "${var.function_name}-s3-read"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject"]
      Resource = "arn:aws:s3:::${var.s3_bucket}/*"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_secrets" {
  count = var.secret_arn != "" ? 1 : 0
  name  = "${var.function_name}-secrets-read"
  role  = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = var.secret_arn
    }]
  })
}

resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = var.handler
  runtime          = var.runtime
  s3_bucket        = var.s3_bucket
  s3_key           = var.s3_key
  source_code_hash = var.source_code_hash

  environment {
    variables = merge(
      { ENVIRONMENT = var.environment },
      var.s3_bucket != "" ? { S3_BUCKET = var.s3_bucket } : {},
      var.secret_arn != "" ? { SECRET_ARN = var.secret_arn } : {}
    )
  }

  tags = { Project = "todo-app", ManagedBy = "terraform" }
}