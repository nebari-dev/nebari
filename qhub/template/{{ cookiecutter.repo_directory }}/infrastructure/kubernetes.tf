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

{% if cookiecutter.provider != "local" %}
  depends_on = [
    module.kubernetes
  ]
{% endif %}
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


module "external-container-reg" {
  source = "./modules/extcr"

  count = {{ cookiecutter.external_container_reg.enabled | default(false,true) | jsonify }} ? 1 : 0

  namespace         = var.environment
  access_key_id     = "{{ cookiecutter.external_container_reg.access_key_id | default("",true) }}"
  secret_access_key = "{{ cookiecutter.external_container_reg.secret_access_key | default("",true) }}"
  extcr_account     = "{{ cookiecutter.external_container_reg.extcr_account | default("",true) }}"
  extcr_region      = "{{ cookiecutter.external_container_reg.extcr_region | default("",true) }}"
}


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


  depends_on = [
    module.kubernetes-ingress,
    module.external-container-reg
  ]
}

provider "keycloak" {
  client_id = "admin-cli"
  username  = "qhub-bot"
  password  = random_password.keycloak-qhub-bot-password.result
  url       = "https://${var.endpoint}"

  tls_insecure_skip_verify = local.tls-insecure-skip-verify
}

module "kubernetes-keycloak-config" {
  source = "./modules/kubernetes/keycloak-config"

  name = var.name

  realm_display_name = {{ cookiecutter.security.keycloak.realm_display_name | default("QHub ${var.name}", true) | jsonify }}

  external-url = var.endpoint

  forwardauth-callback-url-path      = local.forwardauth-callback-url-path
  forwardauth-keycloak-client-id     = local.forwardauth-keycloak-client-id
  forwardauth-keycloak-client-secret = random_password.forwardauth-jhsecret.result

  jupyterhub-callback-url-path   = local.jupyterhub-callback-url-path
  jupyterhub-logout-redirect-url = "{{ cookiecutter.final_logout_uri }}"

  jupyterhub-keycloak-client-id     = local.jupyterhub-keycloak-client-id
  jupyterhub-keycloak-client-secret = random_password.jupyterhub-jhsecret.result

  {% if cookiecutter.security.authentication.type == "GitHub" -%}
  github_client_id     = {{ cookiecutter.security.authentication.config.client_id | jsonify }}
  github_client_secret = {{ cookiecutter.security.authentication.config.client_secret | jsonify }}
  {%- endif %}

  {% if cookiecutter.security.authentication.type == "Auth0" -%}
  auth0_client_id     = {{ cookiecutter.security.authentication.config.client_id | jsonify }}
  auth0_client_secret = {{ cookiecutter.security.authentication.config.client_secret | jsonify }}
  # auth0_subdomain should be for example dev-5xltvsfy.eu or qhub-dev (i.e. without auth0.com at the end)
  auth0_subdomain     = {{ cookiecutter.security.authentication.config.auth0_subdomain | jsonify }}
  {%- endif %}

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

  jupyterhub-overrides = concat([
    file("jupyterhub.yaml")
    ]
{%- if cookiecutter.jupyterhub is defined and cookiecutter.jupyterhub.overrides is defined %},
[<<EOT
{{ cookiecutter.jupyterhub.overrides | default({}) | yamlify -}}
    EOT
    ]
{%- endif %}
  )

{%- if cookiecutter.jupyterhub is defined and cookiecutter.jupyterhub.overrides is defined and cookiecutter.jupyterhub.overrides.hub is defined and cookiecutter.jupyterhub.overrides.hub.extraEnv is defined %}
  jupyterhub-hub-extraEnv = {{- cookiecutter.jupyterhub.overrides.hub.extraEnv | default({}) | jsonify -}}
{%- endif %}

  dask_gateway_extra_config = file("dask_gateway_config.py.j2")

  forwardauth-callback-url-path = local.forwardauth-callback-url-path

  OAUTH_CLIENT_ID        = local.jupyterhub-keycloak-client-id
  OAUTH_CLIENT_SECRET    = random_password.jupyterhub-jhsecret.result
  OAUTH_CALLBACK_URL     = "https://${var.endpoint}${local.jupyterhub-callback-url-path}"
  OAUTH2_TLS_VERIFY      = local.tls-insecure-skip-verify ? "false" : "true"
  keycloak_authorize_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/auth"
  keycloak_token_url     = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/token"
  keycloak_userdata_url  = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/userinfo"
  keycloak_logout_url    = format("%s?redirect_uri=%s", "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/logout", urlencode("{{ cookiecutter.final_logout_uri }}"))

  keycloak_username   = "qhub-bot"
  keycloak_password   = random_password.keycloak-qhub-bot-password.result
  keycloak_server_url = "http://keycloak-headless.${var.environment}:8080/auth/"

  depends_on = [
    module.kubernetes-initialization
  ]
}

{% for helm_extension in cookiecutter.helm_extensions -%}
module "{{helm_extension['name'] }}-extension" {
  source       = "./modules/kubernetes/services/helm-extensions"
  name       = "{{ helm_extension['name'] }}"
  namespace  = var.environment
  repository = "{{ helm_extension['repository'] }}"
  chart      = "{{ helm_extension['chart'] }}"
  chart_version    = "{{ helm_extension['version'] }}"
  {% if 'overrides' in helm_extension -%}
  overrides = [<<EOT
{{ helm_extension['overrides']|yamlify -}}
    EOT
    ]
  {% endif -%}
  depends_on = [
    module.qhub
  ]
}

{% endfor -%}

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
  depends_on = [
    module.kubernetes-initialization
  ]
}

resource "kubernetes_secret" "qhub_yaml_secret" {
  metadata {
    name      = "qhub-config-yaml"
    namespace = var.environment
  }

  data = {
    "qhub-config.yaml" = file({{ cookiecutter.qhub_config_yaml_path | jsonify }})
  }
}
