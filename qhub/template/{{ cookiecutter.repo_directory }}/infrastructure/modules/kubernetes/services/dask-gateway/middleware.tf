resource "kubernetes_manifest" "gateway-middleware" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "qhub-dask-gateway-gateway-api"
      namespace = var.namespace
    }
    spec = {
      stripPrefixRegex = {
        regex = [
          "/gateway"
        ]
      }
    }
  }
}


resource "kubernetes_manifest" "cluster-middleware" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "qhub-dask-gateway-cluster"
      namespace = var.namespace
    }
    spec = {
      stripPrefixRegex = {
        regex = [
          "/gateway/clusters/[a-zA-Z0-9.-]+"
        ]
      }
    }
  }
}
