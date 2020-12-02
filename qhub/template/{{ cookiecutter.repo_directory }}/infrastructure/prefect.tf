
resource "helm_release" "prefect" {
  name      = "prefect"
  namespace = var.environment
  chart     = "../charts/prefect"

  set_sensitive {
    name  = "prefectToken"
    value = var.prefect_token
  }

  set_sensitive {
    name  = "jupyterHubToken"
    value = module.qhub.jupyterhub_api_token
  }

  depends_on = [
    module.kubernetes-ingress.depended_on
  ]
}
