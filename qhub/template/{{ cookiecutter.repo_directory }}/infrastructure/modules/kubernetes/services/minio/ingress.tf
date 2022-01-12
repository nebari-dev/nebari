resource "kubernetes_manifest" "minio-middleware" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "minio-middleware"
      namespace = var.namespace
    }
    spec = {
      stripPrefixRegex = {
        regex = [
          "/minio"
        ]
      }
    }
  }
}

resource "kubernetes_manifest" "minio-web" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "minio-web"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["minio"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${var.external-url}`) && PathPrefix(`/minio`)"
          middlewares = local.minio_middleware
          services = [
            {
              name      = module.minio.service
              port      = 9000
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}
