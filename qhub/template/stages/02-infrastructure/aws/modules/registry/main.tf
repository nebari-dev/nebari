resource "aws_ecr_repository" "main" {
  name = var.name

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge({ Name = var.name }, var.tags)
}
