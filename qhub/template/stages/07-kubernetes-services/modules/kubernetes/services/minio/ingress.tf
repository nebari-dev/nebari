resource "kubernetes_manifest" "minio-api" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "minio-api"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["minio"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`)"
          services = [
            {
              name      = helm_release.minio.name
              port      = 9000
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
