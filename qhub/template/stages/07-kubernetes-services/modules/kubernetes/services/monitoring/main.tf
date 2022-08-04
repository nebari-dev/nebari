resource "helm_release" "prometheus-grafana" {
  name       = "qhub"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "30.1.0"

  values = concat([
    file("${path.module}/values.yaml"),
    # https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/values.yaml
    jsonencode({
      alertmanager = {
        alertmanagerSpec = {
          nodeSelector : {
            "${var.node-group.key}" = var.node-group.value
          }
        }
      }

      prometheusOperator = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }

        admissionWebhooks = {
          patch = {
            nodeSelector = {
              "${var.node-group.key}" = var.node-group.value
            }
          }
        }
      }

      kube-state-metrics = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

      prometheus = {
        prometheusSpec = {
          nodeSelector = {
            "${var.node-group.key}" = var.node-group.value
          }
        }
      }

      # https://github.com/grafana/helm-charts/blob/main/charts/grafana/values.yaml
      grafana = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }

        "grafana.ini" : {
          server = {
            protocol            = "http"
            domain              = var.external-url
            root_url            = "https://%(domain)s/monitoring"
            serve_from_sub_path = "true"
          }

          auth = {
            oauth_auto_login = "true"
          }

          "auth.generic_oauth" = {
            enabled                  = "true"
            name                     = "Login Keycloak"
            allow_sign_up            = "true"
            client_id                = module.grafana-client-id.config.client_id
            client_secret            = module.grafana-client-id.config.client_secret
            scopes                   = "profile"
            auth_url                 = module.grafana-client-id.config.authentication_url
            token_url                = module.grafana-client-id.config.token_url
            api_url                  = module.grafana-client-id.config.userinfo_url
            tls_skip_verify_insecure = "true"
            login_attribute_path     = "preferred_username"
            role_attribute_path      = "contains(roles[*], 'grafana_admin') && 'Admin' || contains(roles[*], 'grafana_developer') && 'Editor' || contains(roles[*], 'grafana_viewer') || 'Viewer'"
          }
        }
      }
    })
  ], var.overrides)
}


module "grafana-client-id" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "grafana"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["grafana_admin"]
    "developer" = ["grafana_developer"]
    "analyst"   = ["grafana_viewer"]
  }
  callback-url-paths = [
    "https://${var.external-url}/monitoring/login/generic_oauth"
  ]
}


resource "kubernetes_config_map" "dashboard" {
  metadata {
    name      = "qhub-grafana-dashboards"
    namespace = var.namespace
    labels = {
      # grafana_dashboard label needed for grafana to pick it up
      # automatically
      grafana_dashboard = "1"
    }
  }

  data = {
    for dashboard in var.dashboards : dashboard => file("${path.module}/dashboards/${dashboard}")
  }
}


resource "kubernetes_manifest" "grafana-ingress-route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "grafana-ingress-route"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/monitoring`)"
          services = [
            {
              name      = "qhub-grafana"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
