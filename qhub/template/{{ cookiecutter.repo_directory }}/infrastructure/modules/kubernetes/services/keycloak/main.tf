resource "helm_release" "keycloak" {
  name      = "keycloak"
  namespace = var.namespace

  repository = "https://codecentric.github.io/helm-charts"
  chart      = "keycloak"
  version    = "14.0.1"

  values = concat([
    file("${path.module}/values.yaml"),
  ], var.overrides)

  set {
    name  = "ingress.rules[0].host"
    value = var.external-url
  }
}


resource "kubernetes_manifest" "keycloak-http" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "keycloak-http"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${var.external-url}`) && PathPrefix(`/auth`) "
          services = [
            {
              name      = "keycloak-headless"
              port      = 80
              #namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}
