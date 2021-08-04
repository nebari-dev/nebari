{% for ext in cookiecutter.extensions | default([]) %}

#### Extension: {{ ext.name }} ####

module "ext-{{ ext.name }}" {
  source = "./modules/kubernetes/qhubextension"

  name         = "qhub-ext-{{ ext.name }}"
  namespace    = var.environment
  image        = "{{ ext.image }}"
  urlslug      = "{{ ext.urlslug }}"
  private      = {{ ext.private | jsonify }}
  external-url = var.endpoint
}

{% endfor %}