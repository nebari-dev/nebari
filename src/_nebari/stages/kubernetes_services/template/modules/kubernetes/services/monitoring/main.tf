resource "random_password" "grafana_admin_password" {
  length  = 32
  special = false
}

resource "kubernetes_secret" "grafana_oauth_secret" {
  metadata {
    name      = "grafana-oauth-secret"
    namespace = var.namespace
  }

  data = {
    "grafana-oauth-client-id"     = module.grafana-client-id.config.client_id
    "grafana-oauth-client-secret" = module.grafana-client-id.config.client_secret
  }
}

resource "helm_release" "prometheus-grafana" {
  name       = "nebari"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "58.4.0"

  values = concat([
    file("${path.module}/values.yaml"),
    # https://github.com/prometheus-community/helm-charts/blob/kube-prometheus-stack-58.4.0/charts/kube-prometheus-stack/values.yaml
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
        # kube-state-metrics does not collect pod labels by default.
        # This tells kube-state-metrics to collect app and component labels which are used by the jupyterhub grafana dashboards.
        metricLabelsAllowlist = ["pods=[app,component,hub.jupyter.org/username,app.kubernetes.io/component,gateway.dask.org/cluster]", "nodes=[*]"] # ["pods=[*]"] would collect all pod labels, but is not recommended.
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

      prometheus = {
        prometheusSpec = {
          nodeSelector = {
            "${var.node-group.key}" = var.node-group.value
          }
          additionalScrapeConfigs = [
            {
              job_name        = "kuberhealthy"
              scrape_interval = "1m"
              honor_labels    = true
              metrics_path    = "/metrics"
              static_configs = [
                {
                  targets = [
                    "kuberhealthy.${var.namespace}.svc.cluster.local"
                  ]
                }
              ]
            },
            {
              job_name     = "Keycloak Target"
              metrics_path = "/auth/realms/master/metrics"
              static_configs = [
                { targets = [
                  "keycloak-http.${var.namespace}.svc",
                  ]
                }
              ]
            },
            {
              job_name     = "Conda Store Target"
              metrics_path = "/conda-store/metrics"
              static_configs = [
                { targets = [
                  "nebari-conda-store-server.${var.namespace}.svc:5000",
                  ]
                }
              ]
            },
            {
              job_name     = "Jupyterhub"
              metrics_path = "/hub/metrics"
              static_configs = [
                { targets = [
                  "hub.${var.namespace}.svc:8081",
                  ]
                }
              ]
              authorization = {
                type        = "Bearer"
                credentials = var.jupyterhub_api_token
              }
            },
            {
              "job_name"     = "Kubernetes Services"
              "honor_labels" = true
              "kubernetes_sd_configs" = [{
                "role" = "endpoints"
              }]

              "relabel_configs" = [
                {
                  "action" = "keep"

                  "regex" = true

                  "source_labels" = ["__meta_kubernetes_service_annotation_prometheus_io_scrape"]
                },
                {
                  "action" = "drop"

                  "regex" = true

                  "source_labels" = ["__meta_kubernetes_service_annotation_prometheus_io_scrape_slow"]
                },
                {
                  "action" = "replace"

                  "regex" = "(https?)"

                  "source_labels" = ["__meta_kubernetes_service_annotation_prometheus_io_scheme"]

                  "target_label" = "__scheme__"
                },
                {
                  "action" = "replace"

                  "regex" = "(.+)"

                  "source_labels" = ["__meta_kubernetes_service_annotation_prometheus_io_path"]

                  "target_label" = "__metrics_path__"
                },
                {
                  "action" = "replace"

                  "regex" = "(.+?)(?::\\d+)?;(\\d+)"

                  "replacement" = "$1:$2"

                  "source_labels" = ["__address__", "__meta_kubernetes_service_annotation_prometheus_io_port"]

                  "target_label" = "__address__"
                },
                {
                  "action" = "labelmap"

                  "regex" = "__meta_kubernetes_service_annotation_prometheus_io_param_(.+)"

                  "replacement" = "__param_$1"
                },
                {
                  "action" = "labelmap"

                  "regex" = "__meta_kubernetes_service_label_(.+)"
                },
                {
                  "action" = "replace"

                  "source_labels" = ["__meta_kubernetes_namespace"]

                  "target_label" = "namespace"
                },
                {
                  "action" = "replace"

                  "source_labels" = ["__meta_kubernetes_service_name"]

                  "target_label" = "service"
                },
                {
                  "action" = "replace"

                  "source_labels" = ["__meta_kubernetes_pod_node_name"]

                  "target_label" = "node"
                }
              ]
            }
          ]
        }
      }

      # https://github.com/grafana/helm-charts/blob/main/charts/grafana/values.yaml
      grafana = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }

        additionalDataSources = [
          {
            name = "Loki"
            type = "loki"
            url  = "http://loki-gateway.${var.namespace}"
          }
        ]

        # Avoid using the default password, as that's a security risk
        adminPassword : random_password.grafana_admin_password.result

        sidecar = {
          dashboards = {
            annotations = {
              "dashboard/subdirectory" = "Supplementary"
            }
            provider = {
              foldersFromFilesStructure : true
            }
            # If specified, the sidecar will look for annotation with this name to create folder and put graph here.
            # You can use this parameter together with `provider.foldersFromFilesStructure`to annotate configmaps and create folder structure.
            folderAnnotation : "dashboard/subdirectory"
          }
        }

        envFromSecret = kubernetes_secret.grafana_oauth_secret.metadata[0].name

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
            client_id                = "$__env{grafana-oauth-client-id}"
            client_secret            = "$__env{grafana-oauth-client-secret}"
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
  for_each = var.dashboards
  metadata {
    name      = "nebari-grafana-dashboards-${lower(each.value)}"
    namespace = var.namespace
    labels = {
      # grafana_dashboard label needed for grafana to pick it up
      # automatically
      grafana_dashboard = "1"
    }
    annotations = {
      "dashboard/subdirectory" = "${each.value}"
    }
  }

  data = {
    for dashboard_file in fileset("${path.module}/dashboards/${each.value}", "*.json") :
    dashboard_file => file("${path.module}/dashboards/${each.value}/${dashboard_file}")
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
              name      = "nebari-grafana"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
