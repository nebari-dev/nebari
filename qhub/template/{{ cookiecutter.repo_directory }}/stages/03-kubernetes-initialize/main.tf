module "kubernetes-initialization" {
  source = "./modules/kubernetes/initialization"

  namespace = var.environment
  secrets   = []
}

module "kubernetes-autoscaling" {
  count = var.qhub_config.provider == "aws" ? 1 : 0

  source = "./modules/kubernetes/services/cluster-autoscaler"

  namespace = var.environment

  aws-region   = var.qhub_config.amazon_web_services.region
  cluster-name = local.cluster_name
}

module "external-container-reg" {
  count = var.external_container_reg.enabled ? 1 : 0

  source = "./modules/extcr"

  namespace         = var.environment
  access_key_id     = var.external_container_reg.access_key_id
  secret_access_key = var.external_container_reg.secret_access_key
  extcr_account     = var.external_container_reg.extcr_account
  extcr_region      = var.external_container_reg.extcr_region
}

resource "kubernetes_secret" "qhub_yaml_secret" {
  metadata {
    name      = "qhub-config-yaml"
    namespace = var.environment
  }

  data = {
    "qhub-config.yaml" = yamlencode(var.qhub_config)
  }
}

module "traefik-crds" {
  source = "./modules/kubernetes/traefik_crds"
}
