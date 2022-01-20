resource "random_password" "keycloak-qhub-bot-password" {
  length  = 32
  special = false
}

module "kubernetes-keycloak-helm" {
  source = "./modules/kubernetes/keycloak-helm"

  namespace = var.environment

  external-url = var.endpoint

  qhub-bot-password = random_password.keycloak-qhub-bot-password.result

  initial-root-password = {{ cookiecutter.security.get('keycloak',{}).initial_root_password | default("password",true) | jsonify }}

  # Be careful that overrides don't clobber anything important.
  # For example, if extraEnv is present, it should repeat PROXY_ADDRESS_FORWARDING from values.yaml.
  {% if cookiecutter.security.keycloak is defined and cookiecutter.security.keycloak.overrides is defined %}
  overrides            = [<<EOT
{{ cookiecutter.security.keycloak.overrides|yamlify -}}
    EOT
    ]
  {% endif %}
}
