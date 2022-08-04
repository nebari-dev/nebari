resource "kubernetes_config_map" "dask-etc" {
  metadata {
    name      = "dask-etc"
    namespace = var.namespace
  }

  data = {
    "gateway.yaml" = jsonencode({
      gateway = {
        address        = "http://${kubernetes_service.gateway.metadata.0.name}.${kubernetes_service.gateway.metadata.0.namespace}:8000"
        public_address = "https://${var.external-url}/gateway"
        proxy_address  = "tcp://${var.external-url}:8786"

        auth = {
          type = "jupyterhub"
        }
      }
    })
    "dashboard.yaml" = jsonencode({})
  }
}

resource "kubernetes_manifest" "dask-gateway" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "dask-gateway"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/gateway/`)"

          middlewares = [
            {
              name      = "qhub-dask-gateway-gateway-api"
              namespace = var.namespace
            }
          ]

          services = [
            {
              name = kubernetes_service.gateway.metadata.0.name
              port = 8000
            }
          ]
        }
      ]
    }
  }
}
