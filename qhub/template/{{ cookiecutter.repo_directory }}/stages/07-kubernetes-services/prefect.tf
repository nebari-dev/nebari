{% if cookiecutter.prefect.enabled -%}
module "prefect" {
  source = "./modules/kubernetes/services/prefect"

  namespace            = var.environment
  jupyterhub_api_token = module.jupyterhub.services.prefect.api_token
  prefect_token        = var.prefect_token
  {% if cookiecutter.prefect.image is defined -%}
  image                = "{{ cookiecutter.prefect.image }}"
  {% endif -%}
  {% if cookiecutter.prefect.overrides is defined %}
  overrides            = [<<EOT
{{ cookiecutter.prefect.overrides|yamlify -}}
    EOT
    ]
  {% endif %}
}
{% endif -%}
