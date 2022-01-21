resource "random_password" "service_token" {
  for_each = var.services

  length  = 32
  special = false
}

resource "random_password" "proxy_secret_token" {
  length  = 32
  special = false
}

resource "helm_release" "jupyterhub" {
  name      = "jupyterhub"
  namespace = var.namespace

  repository = "https://jupyterhub.github.io/helm-chart/"
  chart      = "jupyterhub"
  version    = "1.2.0"

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      # custom values can be accessed via z2jh.get_config('custom.<path>')
      custom = {
        jupyterhub-theme = var.jupyterhub-theme
        cdsdashboards    = var.cdsdashboards
      }

      hub = {
        image = var.jupyterhub-image

        extraConfig = {
          "01-theme" = file("${path.module}/files/theme.py")
          "02-spawner" = file("${path.module}/files/spawner.py")
        }

        services = {
          for service in var.services: service => {
            name = service
            admin = true
            api_token = random_password.service_token[service].result
          }
        }
        config = {
          JupyterHub = {
            authenticator_class = "generic-oauth"
          }
          Authenticator = {
            enable_auth_state = true
          }
          GenericOAuthenticator = {
            client_id = module.jupyterhub-openid-client.config.client_id
            client_secret = module.jupyterhub-openid-client.config.client_secret
            oauth_callback_url = "https://${var.external-url}/hub/oauth_callback"
            authorize_url = module.jupyterhub-openid-client.config.authentication_url
            token_url = module.jupyterhub-openid-client.config.token_url
            userdata_url = module.jupyterhub-openid-client.config.userinfo_url
            login_service = "keycloak"
            username_key = "preferred_username"
            claim_groups_key = "roles"
            allowed_groups = ["jupyterhub_admin", "jupyterhub_developer"]
            admin_groups = ["jupyterhub_admin"]
            tls_verify = false
          }
        }
      }

      singleuser = {
        image = var.jupyterlab-image

        storage = {
          static = {
            pvcName = var.home-pvc
            subPath = "home/{username}"
          }

          extraVolumes = concat(
            [
              for k, v in var.extra-mounts: {
                name = v.name
                persistentVolumeClaim = {
                  claimName = v.name
                }
              } if v.kind == "persistentvolumeclaim"
            ],
            [
              for k, v in var.extra-mounts: {
                name = v.name
                configMap = {
                  name = v.name
                }
              } if v.kind == "configmap"
            ])

          extraVolumeMounts = [
            for k, v in var.extra-mounts: {
              name = v.name
              mountPath = k
            }
          ]
        }
      }
    })
  ], var.overrides)

  set {
    name  = "proxy.secretToken"
    value = random_password.proxy_secret_token.result
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
        }
      ]
      tls = {}
    }
  }
}


module "jupyterhub-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id  = "jupyterhub"
  external-url = var.external-url
  role_mapping = {
    "jupyterhub_admin" = "admin"
    "jupyterhub_developer" = "developer"
  }
  callback-url-paths = [
    "https://${var.external-url}/hub/oauth_callback"
  ]
}
