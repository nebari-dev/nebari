provider "aws" {
  region = "{{ cookiecutter.amazon_web_services.region }}"
}

data "aws_availability_zones" "awszones" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# ==================== ACCOUNTING ======================
module "accounting" {
  source = "./modules/aws/accounting"

  project     = var.name
  environment = var.environment

  tags = local.additional_tags
}


# ======================= NETWORK ======================
module "network" {
  source = "./modules/aws/network"

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
  aws_availability_zones = length(var.availability_zones) >= 2 ? var.availability_zones : [data.aws_availability_zones.awszones.names[0], data.aws_availability_zones.awszones.names[1]]
}


# ==================== REGISTRIES =====================
module "registry-jupyterlab" {
  source = "./modules/aws/registry"

  name = "${local.cluster_name}-jupyterlab"
  tags = local.additional_tags
}


# ====================== EFS =========================
module "efs" {
  source = "./modules/aws/efs"

  name = "${local.cluster_name}-jupyterhub-shared"
  tags = local.additional_tags

  efs_subnets         = module.network.subnet_ids
  efs_security_groups = [module.network.security_group_id]
}


# ==================== KUBERNETES =====================
module "kubernetes" {
  source = "./modules/aws/kubernetes"

  name = local.cluster_name
  tags = local.additional_tags

  cluster_subnets         = module.network.subnet_ids
  cluster_security_groups = [module.network.security_group_id]

  node_group_additional_policies = [
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  ]

  node_groups = [
{% for nodegroup, nodegroup_config in cookiecutter.amazon_web_services.node_groups.items() %}
    {
      name          = "{{ nodegroup }}"
      instance_type = "{{ nodegroup_config.instance }}"
      min_size      = {{ nodegroup_config.min_nodes }}
      desired_size  = {{ nodegroup_config.min_nodes }}
      max_size      = {{ nodegroup_config.max_nodes }}
      gpu           = {{ "true" if nodegroup_config.gpu is defined and nodegroup_config.gpu else "false"}}
    },
{% endfor %}
  ]

  depends_on = [
    module.network
  ]
}
