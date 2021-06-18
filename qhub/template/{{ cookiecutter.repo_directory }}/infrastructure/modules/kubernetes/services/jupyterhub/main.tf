resource "random_password" "proxy_secret_token" {
  length  = 32
  special = false
}

resource "helm_release" "jupyterhub" {
  name      = "jupyterhub"
  namespace = var.namespace

  repository = "https://jupyterhub.github.io/helm-chart/"
  chart      = "jupyterhub"
  version    = "0.9.0-beta.3"

  values = concat([
    file("${path.module}/values.yaml"),
  ], var.overrides)

  set {
    name  = "proxy.secretToken"
    value = random_password.proxy_secret_token.result
  }
}
