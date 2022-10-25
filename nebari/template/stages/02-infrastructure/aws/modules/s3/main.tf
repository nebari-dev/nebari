resource "aws_s3_bucket" "main" {
  bucket = var.name
  acl    = var.public ? "public-read" : "private"

  versioning {
    enabled = true
  }

  tags = merge({
    Name        = var.name
    Description = "S3 bucket for ${var.name}"
  }, var.tags)
}
