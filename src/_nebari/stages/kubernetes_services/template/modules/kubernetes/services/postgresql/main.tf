resource "random_password" "root_password" {
  length  = 32
  special = false
}


resource "helm_release" "postgresql" {
  name      = "${var.name}-postgresql"
  namespace = var.namespace

  repository = "https://raw.githubusercontent.com/bitnami/charts/defb094c658024e4aa8245622dab202874880cbc/bitnami"
  chart      = "postgresql"
  version    = "10.13.12"

  set {
    name  = "postgresqlUsername"
    value = "postgres"
  }

  set {
    name  = "postgresqlPassword"
    value = random_password.root_password.result
  }

  set {
    name  = "postgresqlDatabase"
    value = var.database
  }

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      # TODO: Remove hardcoded image values after Helm chart update
      # This is a workaround due to bitnami charts deprecation
      # See: https://github.com/bitnami/charts/issues/35164
      # See: https://github.com/nebari-dev/nebari/issues/3120
      image = {
        registry   = "docker.io"
        repository = "bitnamilegacy/postgresql"
        tag        = "11.14.0"
      }
      primary = {
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }
    })
  ], var.overrides)
}
