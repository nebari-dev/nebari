resource "random_password" "root_password" {
  length  = 32
  special = false
}


resource "helm_release" "redis" {
  name      = "${var.name}-redis"
  namespace = var.namespace

  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  version    = "17.0.6"

  set {
    name  = "auth.password"
    value = random_password.root_password.result
  }

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      architecture = "standalone"
      master = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }
    })
  ], var.overrides)
}
