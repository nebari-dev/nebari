resource "random_password" "service_token" {
  for_each = var.services

  length  = 32
  special = false
}

resource "random_password" "proxy_secret_token" {
  length  = 32
  special = false
}

resource "random_password" "jhub_apps_jwt_secret" {
  length  = 32
  special = false
}

locals {
  jhub_apps_secrets_name           = "jhub-apps-secrets"
  jhub_apps_env_var_name           = "JHUB_APP_JWT_SECRET_KEY"
  singleuser_nodeselector_key      = var.cloud-provider == "aws" ? "dedicated" : var.user-node-group.key
  userscheduler_nodeselector_key   = var.cloud-provider == "aws" ? "dedicated" : var.general-node-group.key
  userscheduler_nodeselector_value = var.general-node-group.value
}

resource "kubernetes_secret" "jhub_apps_secrets" {
  metadata {
    name      = local.jhub_apps_secrets_name
    namespace = var.namespace
  }

  data = {
    jwt_secret_key = random_password.jhub_apps_jwt_secret.result
  }

  type = "Opaque"
}

locals {
  jupyterhub_env_vars = [
    {
      name = local.jhub_apps_env_var_name,
      valueFrom : {
        secretKeyRef : {
          name : local.jhub_apps_secrets_name
          key : "jwt_secret_key"
        }
      }
    }
  ]
}


resource "helm_release" "jupyterhub" {
  name      = "jupyterhub-${var.namespace}"
  namespace = var.namespace

  repository = "https://jupyterhub.github.io/helm-chart/"
  chart      = "jupyterhub"
  version    = "4.0.0-0.dev.git.6707.h109668fd"

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      # custom values can be accessed via z2jh.get_config('custom.<path>')
      custom = {
        namespace                     = var.namespace
        external-url                  = var.external-url
        theme                         = var.theme
        profiles                      = var.profiles
        argo-workflows-enabled        = var.argo-workflows-enabled
        home-pvc                      = var.home-pvc.name
        shared-pvc                    = var.shared-pvc.name
        conda-store-pvc               = var.conda-store-pvc
        conda-store-mount             = var.conda-store-mount
        default-conda-store-namespace = var.default-conda-store-namespace
        conda-store-service-name      = var.conda-store-service-name
        conda-store-jhub-apps-token   = var.conda-store-jhub-apps-token
        jhub-apps-enabled             = var.jhub-apps-enabled
        initial-repositories          = var.initial-repositories
        skel-mount = {
          name      = kubernetes_config_map.etc-skel.metadata.0.name
          namespace = kubernetes_config_map.etc-skel.metadata.0.namespace
        }
        extra-mounts = merge(
          var.extra-mounts,
          {
            "/etc/ipython" = {
              name      = kubernetes_config_map.etc-ipython.metadata.0.name
              namespace = kubernetes_config_map.etc-ipython.metadata.0.namespace
              kind      = "configmap"
            }

            "/etc/jupyter" = {
              name      = kubernetes_config_map.etc-jupyter.metadata.0.name
              namespace = kubernetes_config_map.etc-jupyter.metadata.0.namespace
              kind      = "configmap"
            }

            "/opt/conda/envs/default/share/jupyter/lab/settings" = {
              name      = kubernetes_config_map.jupyterlab-settings.metadata.0.name
              namespace = kubernetes_config_map.jupyterlab-settings.metadata.0.namespace
              kind      = "configmap"
            }

          }
        )
        environments = var.conda-store-environments
      }

      hub = {
        image = var.jupyterhub-image
        nodeSelector = {
          "${var.general-node-group.key}" = var.general-node-group.value
        }

        extraVolumes = [{
          name = "conda-store-shared"
          persistentVolumeClaim = {
            claimName = var.conda-store-pvc
          }
        }]

        extraVolumeMounts = [{
          mountPath = var.conda-store-mount
          name      = "conda-store-shared"
        }]

        extraConfig = {
          "01-theme.py"    = file("${path.module}/files/jupyterhub/01-theme.py")
          "02-spawner.py"  = file("${path.module}/files/jupyterhub/02-spawner.py")
          "03-profiles.py" = file("${path.module}/files/jupyterhub/03-profiles.py")
          "04-auth.py"     = file("${path.module}/files/jupyterhub/04-auth.py")
        }

        services = {
          for service in var.services : service => {
            name      = service
            admin     = true
            api_token = random_password.service_token[service].result
          }
        }

        # for simple key value configuration with jupyterhub traitlets
        # this hub.config property should be used
        config = {
          Authenticator = {
            enable_auth_state = true
          }
          KeyCloakOAuthenticator = {
            client_id            = module.jupyterhub-openid-client.config.client_id
            client_secret        = module.jupyterhub-openid-client.config.client_secret
            oauth_callback_url   = "https://${var.external-url}/hub/oauth_callback"
            authorize_url        = module.jupyterhub-openid-client.config.authentication_url
            token_url            = module.jupyterhub-openid-client.config.token_url
            userdata_url         = module.jupyterhub-openid-client.config.userinfo_url
            realm_api_url        = module.jupyterhub-openid-client.config.realm_api_url
            login_service        = "Keycloak"
            username_claim       = "preferred_username"
            claim_groups_key     = "groups"
            claim_roles_key      = "roles"
            allowed_groups       = ["/analyst", "/developer", "/admin", "jupyterhub_admin", "jupyterhub_developer"]
            admin_groups         = ["/admin", "jupyterhub_admin"]
            manage_groups        = true
            manage_roles         = true
            refresh_pre_spawn    = true
            validate_server_cert = false

            # deprecated, to be removed (replaced by validate_server_cert)
            tls_verify = false
            # deprecated, to be removed (replaced by username_claim)
            username_key = "preferred_username"
          }
        }
      }

      proxy = {
        chp = {
          nodeSelector = {
            "${var.general-node-group.key}" = var.general-node-group.value
          }
        }
      }

      singleuser = {
        image = var.jupyterlab-image
        nodeSelector = {
          "${local.singleuser_nodeselector_key}" = var.user-node-group.value
        }
      }

      scheduling = {
        userScheduler = {
          nodeSelector = {
            "${local.userscheduler_nodeselector_key}" = local.userscheduler_nodeselector_value
          }
        }
      }
    })],
    var.overrides,
    [jsonencode({
      hub = {
        extraEnv = concat([
          {
            name  = "OAUTH_LOGOUT_REDIRECT_URL",
            value = format("%s?redirect_uri=%s", "https://${var.external-url}/auth/realms/${var.realm_id}/protocol/openid-connect/logout", urlencode(var.jupyterhub-logout-redirect-url))
          },
          ],
          concat(local.jupyterhub_env_vars, jsondecode(var.jupyterhub-hub-extraEnv))
        )
      }
    })]
  )

  set {
    name  = "proxy.secretToken"
    value = random_password.proxy_secret_token.result
  }

  depends_on = [
    var.home-pvc,
    var.shared-pvc,
  ]

  lifecycle {
    replace_triggered_by = [
      null_resource.home-pvc,
    ]
  }

}

resource "null_resource" "home-pvc" {
  triggers = {
    home-pvc = var.home-pvc.id
  }
}

resource "kubernetes_manifest" "jupyterhub" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "jupyterhub"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && (Path(`/`) || PathPrefix(`/hub`) || PathPrefix(`/user`) || PathPrefix(`/services`))"
          services = [
            {
              name = "proxy-public"
              port = 80
            }
          ]
          middlewares = [
            {
              name      = kubernetes_manifest.jupyterhub-proxy-add-slash.manifest.metadata.name
              namespace = var.namespace
            }
          ]
        },
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && (PathPrefix(`/home`) || PathPrefix(`/token`) || PathPrefix(`/admin`))"
          middlewares = [
            {
              name      = kubernetes_manifest.jupyterhub-middleware-addprefix.manifest.metadata.name
              namespace = var.namespace
            }
          ]
          services = [
            {
              name = "proxy-public"
              port = 80
            }
          ]
        }
      ]
    }
  }
}


module "jupyterhub-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "jupyterhub"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["jupyterhub_admin", "dask_gateway_admin"]
    "developer" = ["jupyterhub_developer", "dask_gateway_developer"]
    "analyst"   = ["jupyterhub_developer"]
  }
  client_roles = [
    {
      "name" : "allow-app-sharing-role",
      "description" : "Allow app sharing for apps created via JupyterHub App Launcher (jhub-apps)",
      "groups" : [],
      "attributes" : {
        # grants permissions to share server
        # grants permissions to read other user's names
        # grants permissions to read other groups' names
        # The later two are required for sharing with a group or user
        "scopes" : "shares,read:users:name,read:groups:name"
        "component" : "jupyterhub"
      }
    },
    {
      "name" : "allow-read-access-to-services-role",
      "description" : "Allow read access to services, such that they are visible on the home page e.g. conda-store",
      # Adding it to analyst group such that it's applied to every user.
      "groups" : ["analyst"],
      "attributes" : {
        # grants permissions to read services
        "scopes" : "read:services",
        "component" : "jupyterhub"
      }
    },
    {
      "name" : "allow-group-directory-creation-role",
      "description" : "Grants a group the ability to manage the creation of its corresponding mounted directory.",
      "groups" : ["admin", "analyst", "developer"],
      "attributes" : {
        # grants permissions to mount group folder to shared dir
        "scopes" : "write:shared-mount",
        "component" : "shared-directory"
      }
    },
  ]
  callback-url-paths = [
    "https://${var.external-url}/hub/oauth_callback",
    var.jupyterhub-logout-redirect-url
  ]
  jupyterlab_profiles_mapper = true
  service-accounts-enabled   = true
  service-account-roles = [
    "view-realm", "view-users", "view-clients"
  ]
}


resource "kubernetes_secret" "argo-workflows-conda-store-token" {
  metadata {
    name      = "argo-workflows-conda-store-token"
    namespace = var.namespace
  }

  data = {
    "conda-store-api-token"         = var.conda-store-argo-workflows-jupyter-scheduler-token
    "conda-store-service-name"      = var.conda-store-service-name
    "conda-store-service-namespace" = var.namespace
  }

  type = "Opaque"
}
