{% for ext in cookiecutter.tf_extensions | default([]) %}

#### Extension: {{ ext.name }} ####

module "ext-{{ ext.name }}" {
  source = "./modules/kubernetes/qhubextension"

  name         = "qhub-ext-{{ ext.name }}"
  namespace    = var.environment
  image        = "{{ ext.image }}"
  urlslug      = "{{ ext.urlslug }}"
  private      = {{ ext.private | jsonify }}
  oauth2client = {{ ext.oauth2client | jsonify }}
  external-url = var.endpoint
  qhub-realm-id = module.kubernetes-keycloak-config.qhub-realm-id

  envs = [
  {% for env in ext.envs | default([]) -%}
    {
      name  = "{{ env.name }}"
      value = {{ env.rawvalue }}
    },
  {% endfor -%}
  ]

  {% if ext.oauth2client %}
  keycloak-client-password = random_password.qhub-ext-{{ ext.name }}-keycloak-client-pw.result
  {% endif %}
  
}

{% if ext.oauth2client %}
resource "random_password" "qhub-ext-{{ ext.name }}-keycloak-client-pw" {
  length  = 32
  special = false
}
{% endif %}

{% endfor %}