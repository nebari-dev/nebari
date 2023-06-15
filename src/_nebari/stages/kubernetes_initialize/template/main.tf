module "kubernetes-initialization" {
  source = "./modules/initialization"

  namespace = var.environment
  secrets   = []
}

module "kubernetes-autoscaling" {
  count = var.cloud_provider == "aws" ? 1 : 0

  source = "./modules/cluster-autoscaler"

  namespace = var.environment

  aws_region   = var.aws_region
  cluster-name = local.cluster_name
}

module "traefik-crds" {
  source = "./modules/traefik_crds"
}

module "nvidia-driver-installer" {
  count = var.gpu_enabled ? 1 : 0

  source = "./modules/nvidia-installer"

  cloud_provider       = var.cloud_provider
  gpu_enabled          = var.gpu_enabled
  gpu_node_group_names = var.gpu_node_group_names
}
