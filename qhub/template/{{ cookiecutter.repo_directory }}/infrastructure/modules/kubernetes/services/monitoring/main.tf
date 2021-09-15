resource "helm_release" "kube-prometheus-stack-helm-deployment" {
  name       = "kube-prometheus-stack"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "16.12.0"

  values = [<<EOT
prometheus:    
  prometheusSpec:    
    additionalScrapeConfigs:    
    
    # This job will scrape from any service with the label app.kubernetes.io/component=traefik-internal-service
    # and the annotation app.kubernetes.io/scrape=true 
    - job_name: 'traefik'    
    
      kubernetes_sd_configs:    
        - role: service    
          
      relabel_configs:    
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]    
        action: keep    
        regex: true    
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]    
        action: replace    
        target_label: __metrics_path__    
        regex: (.+)    
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace    
        regex: ([^:]+)(?::\d+)?;(\d+)    
        replacement: $1:$2    
        target_label: __address__
EOT
  ]

  set {
    name  = "grafana.grafana\\.ini.server.domain"
    value = var.external-url
  }

  set {
    name  = "grafana.grafana\\.ini.server.root_url"
    value = "%(protocol)s://%(domain)s/monitoring"
  }

  set {
    name  = "grafana.grafana\\.ini.server.server_from_sub_path"
    value = "true"
  }
}

resource "kubernetes_manifest" "traefik_dashboard_configmap" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata = {
      name      = "grafana-traefik-dashboard"
      namespace = var.namespace
      labels = {
        # grafana_dashboard label needed for grafana to pick it up automatically
        grafana_dashboard = "1"
      }
    }
    data = {
      "traefik-dashboard.json" = file("${path.module}/traefik.json")
    }
  }
}

resource "kubernetes_manifest" "grafana-strip-prefix-middleware" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "grafana-middleware"
      namespace = var.namespace
    }
    spec = {
      stripPrefixRegex = {
        regex = [
          "/monitoring"
        ]
      }
    }
  }
}


resource "kubernetes_manifest" "grafana-ingress-route" {
  provider = kubernetes-alpha

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
          middlewares = [
            {
              name      = "grafana-middleware"
              namespace = var.namespace
            }
          ]
          services = [
            {
              name      = "kube-prometheus-stack-grafana"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}
