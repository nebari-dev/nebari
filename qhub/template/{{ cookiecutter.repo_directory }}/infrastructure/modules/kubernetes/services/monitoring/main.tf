resource "helm_release" "kube-prometheus-stack-helm-deployment" {
  name       = "kube-prometheus-stack"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "16.12.0"

  set {
    name = "grafana.grafana\\.ini.server.domain"
    value = var.external-url
  }

  set {
    name = "grafana.grafana\\.ini.server.root_url"
    value = "%(protocol)s://%(domain)s/monitoring"
  }

  set {
    name = "grafana.grafana\\.ini.server.server_from_sub_path"
    value = "true"
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
