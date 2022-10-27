module "kubernetes-initialization" {
  source = "./modules/initialization"

  namespace = var.environment
  secrets   = []
}

module "kubernetes-autoscaling" {
  count = var.cloud-provider == "aws" ? 1 : 0

  source = "./modules/cluster-autoscaler"

  namespace = var.environment

  aws-region   = var.aws-region
  cluster-name = local.cluster_name
}

module "traefik-crds" {
  source = "./modules/traefik_crds"
}

module "nvidia-driver-installer" {
  count = var.gpu_enabled ? 1 : 0

  source = "./modules/nvidia-installer"

  cloud-provider       = var.cloud-provider
  gpu_enabled          = var.gpu_enabled
  gpu_node_group_names = var.gpu_node_group_names
}
