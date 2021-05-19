resource "helm_release" "prefect" {
  name      = "prefect"
  namespace = var.namespace
  chart     = "${path.module}/chart"

  set_sensitive {
    name  = "prefectToken"
    value = var.prefect_token
  }

  set_sensitive {
    name  = "jupyterHubToken"
    value = var.jupyterhub_api_token
  }
}
