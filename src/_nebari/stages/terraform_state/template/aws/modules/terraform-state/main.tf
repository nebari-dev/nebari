resource "aws_kms_key" "tf-state-key" {
  enable_key_rotation = true
}

resource "aws_s3_bucket" "terraform-state" {
  bucket = "${var.name}-terraform-state"

  force_destroy = true

  versioning {
    enabled = true
  }

  tags = merge({ Name = "S3 remote terraform state store" }, var.tags)

  lifecycle {
    ignore_changes = [
      server_side_encryption_configuration,
    ]
  }
}

resource "aws_s3_bucket_public_access_block" "terraform-state" {
  bucket                  = aws_s3_bucket.terraform-state.id
  ignore_public_acls      = true
  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform-state" {
  bucket = aws_s3_bucket.terraform-state.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.tf-state-key.arn
      sse_algorithm     = "aws:kms"
    }
  }
  # // AWS may return HTTP 409 if PutBucketEncryption is called immediately after S3
  # bucket creation. Adding dependency avoids concurrent requests.
  depends_on = [aws_s3_bucket_public_access_block.terraform-state]
}

resource "aws_dynamodb_table" "terraform-state-lock" {
  name = "${var.name}-terraform-state-lock"

  read_capacity  = 1
  write_capacity = 1
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = merge({ Name = "DynamoDB table for locking terraform state store" }, var.tags)
}
