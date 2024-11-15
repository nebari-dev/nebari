resource "kubernetes_manifest" "backup-restore-api" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "backup-restore-api"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["backup-restore"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`)"
          services = [
            {
              name      = kubernetes_deployment.backup_restore.metadata.0.name
              port      = 9000
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
