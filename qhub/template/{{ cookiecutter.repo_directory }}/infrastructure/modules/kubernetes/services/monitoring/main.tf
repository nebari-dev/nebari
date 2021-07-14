resource "helm_release" "kube-prometheus-stack-helm-deployment" {
  name              = "kube-prometheus-stack"
  namespace         = var.namespace
  chart             = "${path.module}/chart"
  dependency_update = true
  values            = [file("${path.module}/chart/values-monitoring-qhub.yaml")]

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
      name      = "prometheus-grafana-metadata"
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
              name      = "prometheus-grafana"
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
