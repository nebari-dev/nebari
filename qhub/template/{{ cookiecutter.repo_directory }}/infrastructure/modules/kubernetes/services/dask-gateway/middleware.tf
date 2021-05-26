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

# Create one chain middleware for the IngressRoutes that will be dynamically created by Dask Gateway
# The chain combines traefik-forward-auth and stripprefix middleware defined below.

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
      chain = {
        middlewares = [
          {
            name      = "traefik-forward-auth"
            namespace = var.namespace
          },
          {
            name      = kubernetes_manifest.cluster-middleware-stripprefix.manifest.metadata.name
            namespace = var.namespace
          }
        ]
      }
    }
  }
}

resource "kubernetes_manifest" "cluster-middleware-stripprefix" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "qhub-dask-gateway-cluster-stripprefix"
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
