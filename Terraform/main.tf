provider "aws" {
  region     = "ap-south-1"
  access_key = "${{ secrets.ACCESS_KEY }}"
  secret_key = "${{ secrets.SECRET_KEY }}"
}

resource "aws_s3_bucket" "bucket" {
  bucket = "my-s3-bucket-for-jenkins"
  }

  resource "aws_s3_object" "object" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "Data.csv"
  source = "Data.csv"
}

resource "aws_db_instance" "myrdsdb" {                                             
  allocated_storage    = 5
  max_allocated_storage = 10
  db_name              = "myrdsdb"
  engine               = "mysql"
  identifier           = "database-1"
  engine_version       = "8.0.40"
  instance_class       = "db.t3.micro"
  username             = "${{ secrets.USERNAME }}"
  password             = "${{ secrets.PASSWORD }}"
  parameter_group_name = "default.mysql8.0"
  storage_type         = "gp2"
  skip_final_snapshot  = true
  publicly_accessible  = true
}

resource "aws_ecr_repository" "image" {
  name                 = "s3-to-rds"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "rds_endpoint" {
  value = aws_db_instance.myrdsdb.endpoint
}

resource "aws_glue_catalog_database" "example" {
  name = "my_glue_database"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_full_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "my_lambda" {
  function_name    = "MyLambdaFunction"
  role             = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  filename        = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout = 30

  depends_on = [aws_iam_role_policy_attachment.ecr_full_access]