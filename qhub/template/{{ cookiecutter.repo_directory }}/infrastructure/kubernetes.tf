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
{% if cookiecutter.provider == "aws" %}
  exec {
    api_version = "client.authentication.k8s.io/v1alpha1"
    args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
    command     = "aws"
  }
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
  source = "./modules/kubernetes/initialization"

  namespace = var.environment
  secrets   = []
}


{% if cookiecutter.provider == "aws" -%}
module "kubernetes-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "nfs-mount"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  nfs_endpoint = module.efs.credentials.dns_name
}
{% else -%}
module "kubernetes-nfs-server" {
  source = "./modules/kubernetes/nfs-server"

  name         = "nfs-server"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  node-group   = local.node_groups.general

  depends_on = [
    module.kubernetes-initialization
  ]
}

module "kubernetes-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

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
  source = "./modules/kubernetes/services/conda-store"

  name              = "qhub"
  namespace         = var.environment
  nfs_capacity      = "{{ cookiecutter.storage.conda_store }}"
  node-group        = local.node_groups.general
  conda-store-image = var.conda-store-image
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
  source = "./modules/kubernetes/nfs-mount"

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
  source = "./modules/kubernetes/services/cluster-autoscaler"

  namespace = var.environment

  aws-region   = var.region
  cluster-name = local.cluster_name

  depends_on = [
    module.kubernetes-initialization
  ]
}
{% endif -%}

module "kubernetes-ingress" {
  source = "./modules/kubernetes/ingress"

  namespace = var.environment

  node-group = local.node_groups.general

{% if cookiecutter.certificate.type == "lets-encrypt" %}
  enable-certificates = true
  acme-email          = "{{ cookiecutter.certificate.acme_email }}"
  acme-server         = "{{ cookiecutter.certificate.acme_server }}"
{% endif %}

  depends_on = [
    module.kubernetes-initialization
  ]
}

### Keycloak

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

  depends_on = [
    module.kubernetes-ingress
  ]
}

provider "keycloak" {
    client_id     = "admin-cli"
    username      = "qhub-bot"
    password      = random_password.keycloak-qhub-bot-password.result
    url           = "https://${var.endpoint}"

    tls_insecure_skip_verify = {% if cookiecutter.provider == "local" %}true{% else %}false{% endif %}
}

module "kubernetes-keycloak-config" {
  source = "./modules/kubernetes/keycloak-config"

  name = var.name

  external-url = var.endpoint

  forwardauth-callback-url-path      = local.forwardauth-callback-url-path
  forwardauth-keycloak-client-id     = local.forwardauth-keycloak-client-id
  forwardauth-keycloak-client-secret = random_password.forwardauth-jhsecret.result

  jupyterhub-callback-url-path      = local.jupyterhub-callback-url-path
  jupyterhub-keycloak-client-id     = local.jupyterhub-keycloak-client-id
  jupyterhub-keycloak-client-secret = random_password.jupyterhub-jhsecret.result

  users = jsondecode("{{ cookiecutter.tf_users | jsonify | replace('"', '\\"') }}")

  groups = jsondecode("{{ cookiecutter.tf_groups | jsonify | replace('"', '\\"') }}")

  user_groups = jsondecode("{{ cookiecutter.tf_user_groups | jsonify | replace('"', '\\"') }}")

  smtp = {
    host : {{ cookiecutter.smtp.host | default("",true) | jsonify }}
    email : {{ cookiecutter.smtp.email | default("",true) | jsonify }}
    username : {{ cookiecutter.smtp.username | default("",true) | jsonify }}
    password : {{ cookiecutter.smtp.password | default("",true) | jsonify }}
  }

  depends_on = [
    module.kubernetes-keycloak-helm
  ]
}

module "qhub" {
  source = "./modules/kubernetes/services/meta/qhub"

  name      = "qhub"
  namespace = var.environment

  home-pvc        = "nfs-mount-${var.environment}-share"
  conda-store-pvc = "conda-store-${var.environment}-share"

  external-url = var.endpoint

  jupyterhub-image   = var.jupyterhub-image
  jupyterlab-image   = var.jupyterlab-image
  dask-worker-image  = var.dask-worker-image
  dask-gateway-image = var.dask-gateway-image

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

  extcr_config = {
    enabled : {{ cookiecutter.external_container_reg.enabled | default(false,true) | jsonify }}
    access_key_id : "{{ cookiecutter.external_container_reg.access_key_id | default("",true) }}"
    secret_access_key : "{{ cookiecutter.external_container_reg.secret_access_key | default("",true) }}"
    extcr_account : "{{ cookiecutter.external_container_reg.extcr_account | default("",true) }}"
    extcr_region : "{{ cookiecutter.external_container_reg.extcr_region | default("",true) }}"
  }

  forwardauth-callback-url-path = local.forwardauth-callback-url-path

  OAUTH_CLIENT_ID = local.jupyterhub-keycloak-client-id
  OAUTH_CLIENT_SECRET = random_password.jupyterhub-jhsecret.result
  OAUTH_CALLBACK_URL = "https://${var.endpoint}${local.jupyterhub-callback-url-path}"
  keycloak_authorize_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/auth"
  keycloak_token_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/token"
  keycloak_userdata_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/userinfo"
  keycloak_logout_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/logout"

  keycloak_username   = "qhub-bot"
  keycloak_password   = random_password.keycloak-qhub-bot-password.result
  keycloak_server_url = "http://keycloak-headless.${var.environment}:8080/auth/"

}

{% if cookiecutter.prefect.enabled -%}
module "prefect" {
  source = "./modules/kubernetes/services/prefect"

  depends_on = [
    module.qhub
  ]
  namespace            = var.environment
  jupyterhub_api_token = module.qhub.jupyterhub_api_token
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

{% if cookiecutter.monitoring.enabled -%}
module "monitoring" {
  source       = "./modules/kubernetes/services/monitoring"
  namespace    = var.environment
  external-url = var.endpoint
  tls          = module.qhub.tls
  depends_on = [
    module.qhub
  ]
}
{% endif -%}


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

resource "random_password" "forwardauth-jhsecret" {
  length  = 32
  special = false
}

resource "random_password" "jupyterhub-jhsecret" {
  length  = 32
  special = false
}

module "forwardauth" {
  source       = "./modules/kubernetes/forwardauth"
  namespace    = var.environment
  external-url = var.endpoint

  jh-client-id      = local.forwardauth-keycloak-client-id
  jh-client-secret  = random_password.forwardauth-jhsecret.result
  callback-url-path = local.forwardauth-callback-url-path
}
resource "kubernetes_config_map" "qhub-userinfo-migration" {
  metadata {
    name      = "qhub-userinfo-migration"
    namespace = var.environment
  }

  data = {
    "initial-users.json" = jsonencode({{ cookiecutter.security.users | jsonify }})
    "initial-groups.json" = jsonencode({{ cookiecutter.security.groups | jsonify }})
  }
}
