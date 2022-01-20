module "kubernetes-initialization" {
  source = "./modules/kubernetes/initialization"

  namespace = var.environment
  secrets   = []
}

{% if cookiecutter.provider == "aws" -%}
module "kubernetes-autoscaling" {
  source = "./modules/kubernetes/services/cluster-autoscaler"

  namespace = var.environment

  aws-region   = var.region
  cluster-name = local.cluster_name

  depends_on = [
    module.kubernetes-initialization
  ]
}
{% endif -%}

module "external-container-reg" {
  source = "./modules/extcr"

  count = {{ cookiecutter.external_container_reg.enabled | default(false,true) | jsonify }} ? 1 : 0

  namespace         = var.environment
  access_key_id     = "{{ cookiecutter.external_container_reg.access_key_id | default("",true) }}"
  secret_access_key = "{{ cookiecutter.external_container_reg.secret_access_key | default("",true) }}"
  extcr_account     = "{{ cookiecutter.external_container_reg.extcr_account | default("",true) }}"
  extcr_region      = "{{ cookiecutter.external_container_reg.extcr_region | default("",true) }}"
}

resource "kubernetes_secret" "qhub_yaml_secret" {
  metadata {
    name      = "qhub-config-yaml"
    namespace = var.environment
  }

  data = {
    "qhub-config.yaml" = file({{ cookiecutter.qhub_config_yaml_path | jsonify }})
  }
}

module "traefik-crds" {
  source = "./modules/kubernetes/traefik_crds"
}
