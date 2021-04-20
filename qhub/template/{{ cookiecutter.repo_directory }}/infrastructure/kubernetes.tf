provider "kubernetes" {
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

provider "kubernetes-alpha" {
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


module "kubernetes-initialization" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/initialization?ref={{ cookiecutter.terraform_modules.rev }}"

  namespace = var.environment
  secrets   = []
}


{% if cookiecutter.provider == "aws" -%}
module "kubernetes-nfs-mount" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/nfs-mount?ref={{ cookiecutter.terraform_modules.rev }}"

  name         = "nfs-mount"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  nfs_endpoint = module.efs.credentials.dns_name

  depends_on = [
    module.kubernetes-nfs-server
  ]
}
{% else -%}
module "kubernetes-nfs-server" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/nfs-server?ref={{ cookiecutter.terraform_modules.rev }}"

  name         = "nfs-server"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  node-group   = local.node_groups.general

  depends_on = [
    module.kubernetes-initialization
  ]
}

module "kubernetes-nfs-mount" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/nfs-mount?ref={{ cookiecutter.terraform_modules.rev }}"

  name         = "nfs-mount"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  nfs_endpoint = module.kubernetes-nfs-server.endpoint_ip

  depends_on = [
    module.kubernetes-nfs-server
  ]
}
{% endif %}

module "kubernetes-conda-store-server" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/services/conda-store?ref={{ cookiecutter.terraform_modules.rev }}"

  name         = "qhub"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.conda_store }}"
  node-group   = local.node_groups.general
  environments = {
{% for key in cookiecutter.environments %}
    "{{ key }}" = file("../environments/{{ key }}")
{% endfor %}
  }

  depends_on = [
    module.kubernetes-initialization
  ]
}

module "kubernetes-conda-store-mount" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/nfs-mount?ref={{ cookiecutter.terraform_modules.rev }}"

  name         = "conda-store"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.conda_store }}"
  nfs_endpoint = module.kubernetes-conda-store-server.endpoint_ip

  depends_on = [
    module.kubernetes-conda-store-server
  ]
}

provider "helm" {
  kubernetes {
{% if cookiecutter.provider == "local" %}
    config_path = "~/.kube/config"
{%- else %}
    load_config_file       = false
    host                   = module.kubernetes.credentials.endpoint
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    {% if cookiecutter.provider == "azure" -%}
    username               = module.kubernetes.credentials.username
    password               = module.kubernetes.credentials.password
    client_certificate     = module.kubernetes.credentials.client_certificate
    client_key             = module.kubernetes.credentials.client_key
    {%- else -%}
    token                  = module.kubernetes.credentials.token
    {%- endif -%}
{% endif %}
  }
}

{% if cookiecutter.provider == "aws" -%}
module "kubernetes-autoscaling" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/services/cluster-autoscaler?ref={{ cookiecutter.terraform_modules.rev }}"

  namespace = var.environment

  aws-region   = var.region
  cluster-name = local.cluster_name

  depends_on = [
    module.kubernetes-initialization
  ]
}
{% endif -%}

module "kubernetes-ingress" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/ingress?ref={{ cookiecutter.terraform_modules.rev }}"

  namespace = var.environment

  node-group = local.node_groups.general

{% if cookiecutter.certificate.type == "lets-encrypt" %}
  enable-certificates = true
  acme-email = "{{ cookiecutter.certificate.acme_email }}"
  acme-server = "{{ cookiecutter.certificate.acme_server }}"
{% endif %}

  depends_on = [
    module.kubernetes-initialization
  ]
}

module "qhub" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/services/meta/qhub?ref={{ cookiecutter.terraform_modules.rev }}"

  name      = "qhub"
  namespace = var.environment

  home-pvc        = module.kubernetes-nfs-mount.persistent_volume_claim.name
  conda-store-pvc = module.kubernetes-conda-store-mount.persistent_volume_claim.name

  external-url = var.endpoint

  jupyterhub-image  = var.jupyterhub-image
  jupyterlab-image  = var.jupyterlab-image
  dask-worker-image = var.dask-worker-image

  general-node-group = local.node_groups.general
  user-node-group    = local.node_groups.user
  worker-node-group  = local.node_groups.worker

{% if cookiecutter.certificate.type == "existing" %}
  certificate-secret-name = "{{ cookiecutter.certificate.secret_name }}"
{% endif %}

  jupyterhub-overrides = [
    file("jupyterhub.yaml")
  ]

  dask_gateway_extra_config = file("dask_gateway_config.py.j2")

  depends_on = [
    module.kubernetes-ingress
  ]
}

{% if cookiecutter.prefect is true -%}
module "prefect" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kubernetes/services/prefect?ref={{ cookiecutter.terraform_modules.rev }}"
  depends_on = [
    module.qhub
  ]
  namespace            = var.environment
  jupyterhub_api_token = module.qhub.jupyterhub_api_token
  prefect_token        = var.prefect_token
}
{% endif -%}
