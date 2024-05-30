resource "kubernetes_manifest" "gateway-middleware" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-dask-gateway-gateway-api"
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

# Create one chain middleware for the IngressRoutes that will be
# dynamically created by Dask Gateway The chain combines
# traefik-forward-auth and stripprefix middleware defined below.

resource "kubernetes_manifest" "chain-middleware" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-dask-gateway-chain" # Updated name to -chain from -cluster to avoid upgrade confusion
      namespace = var.namespace
    }
    spec = {
      chain = {
        middlewares = [
          {
            name      = var.forwardauth_middleware_name
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
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-dask-gateway-cluster-stripprefix"
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
