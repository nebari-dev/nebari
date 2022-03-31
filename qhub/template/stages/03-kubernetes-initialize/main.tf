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
  count = length(var.gpu_node_group_names) == 0 ? 0 : 1

  source = "./modules/nvidia-installer"

  gpu_node_group_names = var.gpu_node_group_names
}
