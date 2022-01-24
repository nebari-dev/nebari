module "kubernetes-ingress" {
  source = "./modules/kubernetes/ingress"

  namespace = var.environment

  node-group = var.node_groups.general

{% if cookiecutter.certificate.type == "lets-encrypt" %}
  enable-certificates = true
  acme-email          = "{{ cookiecutter.certificate.acme_email }}"
  acme-server         = "{{ cookiecutter.certificate.acme_server }}"
{% elif cookiecutter.certificate.type == "existing" %}
  certificate-secret-name = "{{ cookiecutter.certificate.secret_name }}"
{% endif %}
}
