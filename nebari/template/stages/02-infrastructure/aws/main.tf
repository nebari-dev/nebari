data "aws_availability_zones" "awszones" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}


locals {
  subnet_ids        = var.existing_subnet_ids == null ? module.network[0].subnet_ids : var.existing_subnet_ids
  security_group_id = var.existing_security_group_id == null ? module.network[0].security_group_id : var.existing_security_group_id
}

# ==================== ACCOUNTING ======================
module "accounting" {
  source = "./modules/accounting"

  project     = var.name
  environment = var.environment

  tags = local.additional_tags
}


# ======================= NETWORK ======================
module "network" {
  count = (var.existing_subnet_ids == null) && (var.existing_security_group_id == null) ? 1 : 0

  source = "./modules/network"

  name = local.cluster_name

  tags = local.additional_tags

  vpc_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  security_group_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "owned"
  }

  vpc_cidr_block         = var.vpc_cidr_block
  aws_availability_zones = length(var.availability_zones) >= 2 ? var.availability_zones : slice(sort(data.aws_availability_zones.awszones.names), 0, 2)
}


# ==================== REGISTRIES =====================
module "registry-jupyterlab" {
  source = "./modules/registry"

  name = "${local.cluster_name}-jupyterlab"
  tags = local.additional_tags
}


# ====================== EFS =========================
module "efs" {
  source = "./modules/efs"

  name = "${local.cluster_name}-jupyterhub-shared"
  tags = local.additional_tags

  efs_subnets         = local.subnet_ids
  efs_security_groups = [local.security_group_id]
}


# ==================== KUBERNETES =====================
module "kubernetes" {
  source = "./modules/kubernetes"

  name               = local.cluster_name
  tags               = local.additional_tags
  region             = var.region
  kubernetes_version = var.kubernetes_version

  cluster_subnets         = local.subnet_ids
  cluster_security_groups = [local.security_group_id]

  node_group_additional_policies = [
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  ]

  node_groups = var.node_groups

}
