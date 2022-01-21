{% if cookiecutter.clearml.enabled -%}
module "clearml" {
  source       = "./modules/kubernetes/services/clearml"
  namespace    = var.environment
  external-url = var.endpoint
  tls          = module.qhub.tls
{% if cookiecutter.clearml.enable_forward_auth is defined -%}
  enable-forward-auth = {{ cookiecutter.clearml.enable_forward_auth | default(false,true) | jsonify }}
{% endif -%}
  depends_on = [
    module.qhub
  ]
}
{% endif -%}
