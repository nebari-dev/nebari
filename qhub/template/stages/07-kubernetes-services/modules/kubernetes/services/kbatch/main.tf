resource "helm_release" "kbatch" {
  name       = "kbatch"
  namespace  = var.namespace
  chart      = "${path.module}/chart"

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      app = {
        jupyterhub_api_token = var.jupyterhub_api_token
        jupyterhub_api_url = "https://${var.external-url}/hub/api/"
        extra_env = {
          KBATCH_PREFIX = "/services/kbatch"
        }
      }
      image = {
          tag = "0.3.1"
      }
    })
  ])

  set_sensitive {
    name  = "jupyterHubToken"
    value = var.jupyterhub_api_token
  }

  set {
    name  = "kbatchImage"
    value = var.image
  }

  set {
    name  = "namespace"
    value = var.namespace
  }

}
