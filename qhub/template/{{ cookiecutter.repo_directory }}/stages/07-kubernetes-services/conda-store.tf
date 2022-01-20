module "kubernetes-conda-store-server" {
  source = "./modules/kubernetes/services/conda-store"

  name              = "qhub"
  namespace         = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  nfs_capacity      = "{{ cookiecutter.storage.conda_store }}"
  node-group        = local.node_groups.general
  conda-store-image = var.conda-store-image
  environments = {
{% for key in cookiecutter.environments %}
    "{{ key }}" = file("../../environments/{{ key }}")
{% endfor %}
  }
}

module "kubernetes-conda-store-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "conda-store"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.conda_store }}"
  nfs_endpoint = module.kubernetes-conda-store-server.endpoint_ip

  depends_on = [
    module.kubernetes-conda-store-server
  ]
}
