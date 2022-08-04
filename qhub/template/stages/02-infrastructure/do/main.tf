module "kubernetes" {
  source = "./modules/kubernetes"

  name = "${var.name}-${var.environment}"

  region             = var.region
  kubernetes_version = var.kubernetes_version

  node_groups = [
    for name, config in var.node_groups : {
      name       = name
      auto_scale = true
      size       = config.instance
      min_nodes  = config.min_nodes
      max_nodes  = config.max_nodes
    }
  ]

  tags = concat([
    "provision::terraform",
    "project::${var.name}",
    "namespace::${var.environment}",
    "owner::qhub",
  ], var.tags)
}
