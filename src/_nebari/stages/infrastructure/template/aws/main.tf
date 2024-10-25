data "aws_availability_zones" "awszones" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

data "aws_partition" "current" {}

locals {
  # Only override_network if both existing_subnet_ids and existing_security_group_id are not null.
  override_network  = (var.existing_subnet_ids != null) && (var.existing_security_group_id != null)
  subnet_ids        = local.override_network ? var.existing_subnet_ids : module.network[0].subnet_ids
  security_group_id = local.override_network ? var.existing_security_group_id : module.network[0].security_group_id
  partition         = data.aws_partition.current.partition
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
  count = local.override_network ? 0 : 1

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
  count  = var.efs_enabled ? 1 : 0
  source = "./modules/efs"

  name = "${local.cluster_name}-jupyterhub-shared"
  tags = local.additional_tags

  efs_subnets         = local.subnet_ids
  efs_security_groups = [local.security_group_id]
}

moved {
  from = module.efs
  to   = module.efs[0]
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
    "arn:${local.partition}:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  ]

  node_groups = var.node_groups

  endpoint_public_access  = var.eks_endpoint_access == "private" ? false : true
  endpoint_private_access = var.eks_endpoint_access == "public" ? false : true
  public_access_cidrs     = var.eks_public_access_cidrs
  permissions_boundary    = var.permissions_boundary
}
