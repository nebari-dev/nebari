resource "kubernetes_manifest" "nebariextension-ingressroute" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "${var.name}-ingressroute"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/${var.urlslug}/`)"

          # forwardauth middleware may be included via local.middlewares
          middlewares = concat(
            local.middlewares,
            [{
              name      = kubernetes_manifest.nebariextension-middleware.manifest.metadata.name
              namespace = var.namespace
            }]
          )

          services = [
            {
              name = kubernetes_service.nebari-extension-service.metadata[0].name
              port = 80
            }
          ]
        }
      ]
    }
  }
}

# Strip Prefix middleware to remove urlslug

resource "kubernetes_manifest" "nebariextension-middleware" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebariext-middleware-${var.name}"
      namespace = var.namespace
    }
    spec = {
      stripPrefixRegex = {
        regex = [
          "/${var.urlslug}"
        ]
      }
    }
  }
}
