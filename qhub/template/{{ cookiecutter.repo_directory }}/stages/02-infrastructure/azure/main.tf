module "registry" {
  source              = "../modules/azure/registry"

  name                = "${var.name}${var.environment}"
  location            = var.region
  resource_group_name = "${var.name}-${var.environment}"
}


module "kubernetes" {
  source = "../modules/azure/kubernetes"

  name                     = "${var.name}-${var.environment}"
  environment              = var.environment
  location                 = var.region
  resource_group_name      = "${var.name }-${var.environment}"
  node_resource_group_name = "${var.name}-${var.environment}-node-resource-group"
  kubernetes_version       = var.kubernetes_version

  node_groups = [
    for name, config in var.node_groups: {
      name          = name
      auto_scale    = true
      instance_type = config.instance
      min_size      = config.min_size
      max_size      = config.max_size
    }
  ]
}
