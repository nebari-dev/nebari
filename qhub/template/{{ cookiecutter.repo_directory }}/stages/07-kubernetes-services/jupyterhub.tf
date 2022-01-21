{% if cookiecutter.provider == "aws" -%}
module "jupyterhub-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "jupyterhub"
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
}

module "jupyterhub-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "jupyterhub"
  namespace    = var.environment
  nfs_capacity = "{{ cookiecutter.storage.shared_filesystem }}"
  nfs_endpoint = module.kubernetes-nfs-server.endpoint_ip

  depends_on = [
    module.kubernetes-nfs-server
  ]
}
{% endif %}


module "jupyterhub" {
  source = "./modules/kubernetes/services/jupyterhub"

  name      = var.name
  namespace = var.environment

  external-url = var.endpoint
  realm_id = var.realm_id

  home-pvc = module.jupyterhub-nfs-mount.persistent_volume_claim.name

  extra-mounts = {
    "/home/conda" = module.conda-store-nfs-mount.persistent_volume_claim
    "etc/dask"    = {
      name = "dask-etc"
      namespace = var.environment
      kind = "configmap"
    }
  }

  services = [
    "dask-gateway"
    {% if cookiecutter.prefect.enabled -%}"prefect"{% endif %}
  ]

  jupyterhub-image = var.jupyterhub-image
  jupyterlab-image = var.jupyterlab-image

  cdsdashboards    = var.cdsdashboards
  jupyterhub-theme = var.jupyterhub-theme
}


# module "qhub" {
#   source = "./modules/kubernetes/services/meta/qhub"

#   name      = "qhub"
#   namespace = var.environment

#   home-pvc        = "nfs-mount-${var.environment}-share"
#   conda-store-pvc = "conda-store-${var.environment}-share"

#   external-url = var.endpoint

#   jupyterhub-image   = var.jupyterhub-image
#   jupyterlab-image   = var.jupyterlab-image
#   dask-worker-image  = var.dask-worker-image
#   dask-gateway-image = var.dask-gateway-image

#   general-node-group = local.node_groups.general
#   user-node-group    = local.node_groups.user
#   worker-node-group  = local.node_groups.worker

# {% if cookiecutter.certificate.type == "existing" %}
#   certificate-secret-name = "{{ cookiecutter.certificate.secret_name }}"
# {% endif %}

#   jupyterhub-overrides = concat([
#     file("jupyterhub.yaml")
#     ]
# {%- if cookiecutter.jupyterhub is defined and cookiecutter.jupyterhub.overrides is defined %},
# [<<EOT
# {{ cookiecutter.jupyterhub.overrides | default({}) | yamlify -}}
#     EOT
#     ]
# {%- endif %}
#   )

# {%- if cookiecutter.jupyterhub is defined and cookiecutter.jupyterhub.overrides is defined and cookiecutter.jupyterhub.overrides.hub is defined and cookiecutter.jupyterhub.overrides.hub.extraEnv is defined %}
#   jupyterhub-hub-extraEnv = {{- cookiecutter.jupyterhub.overrides.hub.extraEnv | default({}) | jsonify -}}
# {%- endif %}

#   dask_gateway_extra_config = file("dask_gateway_config.py.j2")

#   forwardauth-callback-url-path = local.forwardauth-callback-url-path

#   OAUTH_CLIENT_ID        = local.jupyterhub-keycloak-client-id
#   OAUTH_CLIENT_SECRET    = random_password.jupyterhub-jhsecret.result
#   OAUTH_CALLBACK_URL     = "https://${var.endpoint}${local.jupyterhub-callback-url-path}"
#   OAUTH2_TLS_VERIFY      = local.tls-insecure-skip-verify ? "false" : "true"
#   keycloak_authorize_url = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/auth"
#   keycloak_token_url     = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/token"
#   keycloak_userdata_url  = "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/userinfo"
#   keycloak_logout_url    = format("%s?redirect_uri=%s", "https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/logout", urlencode("{{ cookiecutter.final_logout_uri }}"))

#   keycloak_username   = "qhub-bot"
#   keycloak_password   = random_password.keycloak-qhub-bot-password.result
#   keycloak_server_url = "http://keycloak-headless.${var.environment}:8080/auth/"

#   depends_on = [
#     module.kubernetes-initialization
#   ]
# }
