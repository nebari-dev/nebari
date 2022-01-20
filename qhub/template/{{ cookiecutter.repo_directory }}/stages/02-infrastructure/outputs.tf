output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster"
  value       = {
{% if cookiecutter.provider == "local" %}
    config_path = "~/.kube/config"
{% if cookiecutter.local.kube_context is defined %}
    config_context = "{{ cookiecutter.local.kube_context }}"
{% endif %}
{% elif cookiecutter.provider == "azure" %}
    username               = module.kubernetes.credentials.username
    password               = module.kubernetes.credentials.password
    client_certificate     = module.kubernetes.credentials.client_certificate
    client_key             = module.kubernetes.credentials.client_key
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    host                   = module.kubernetes.credentials.endpoint
{% else %}
    host                   = module.kubernetes.credentials.endpoint
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    token                  = module.kubernetes.credentials.token
{% endif %}
  }
}
