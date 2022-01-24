locals {
  additional_tags = {
    Project     = var.name
    Owner       = "terraform"
    Environment = var.environment
  }

  cluster_name = "${var.name}-${var.environment}"
}
