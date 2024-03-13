locals {
  additional_tags = merge(
    {
      Project     = var.name
      Owner       = "terraform"
      Environment = var.environment
    },
    var.tags,
  )
  cluster_name = "${var.name}-${var.environment}"
}
