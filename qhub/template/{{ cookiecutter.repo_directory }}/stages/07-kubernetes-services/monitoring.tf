{% if cookiecutter.monitoring.enabled -%}
module "monitoring" {
  source       = "./modules/kubernetes/services/monitoring"
  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id
}
{% endif -%}
