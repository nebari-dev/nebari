resource "kubernetes_manifest" "jupyterhub-middleware-addprefix" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-jupyterhub-add-prefix"
      namespace = var.namespace
    }
    spec = {
      addPrefix = {
        prefix = "/hub"
      }
    }
  }
}
