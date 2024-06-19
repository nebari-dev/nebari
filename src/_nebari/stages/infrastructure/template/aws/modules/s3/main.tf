resource "aws_kms_key" "main" {
  description         = "KMS key for ${var.name}"
  enable_key_rotation = true
}

resource "aws_s3_bucket" "main" {
  bucket = var.name
  acl    = var.public ? "public-read" : "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.main.arn
        sse_algorithm     = "aws:kms"
      }
    }

  }

  tags = merge({
    Name        = var.name
    Description = "S3 bucket for ${var.name}"
  }, var.tags)
}
