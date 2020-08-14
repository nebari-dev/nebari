provider "aws" {
  region = "{{ cookiecutter.amazon_web_services.region }}"
}


# ==================== ACCOUNTING ======================
module "accounting" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/accounting"

  project     = var.name
  environment = var.environment
}


# ======================= NETWORK ======================
module "network" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/network"

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
  aws_availability_zones = var.availability_zones
}


# ==================== REGISTRIES =====================
module "registry-jupyterlab" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/registry"

  name = "${local.cluster_name}-jupyterlab"
  tags = local.additional_tags
}


# ====================== EFS =========================
module "efs" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/efs"

  name = "${local.cluster_name}-jupyterhub-shared"
  tags = local.additional_tags

  efs_subnets         = module.network.subnet_ids
  efs_security_groups = [module.network.security_group_id]
}


# ==================== KUBERNETES =====================
module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/kubernetes"

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
    },
{% endfor %}
  ]

  dependencies = [
    module.network.depended_on
  ]
}
