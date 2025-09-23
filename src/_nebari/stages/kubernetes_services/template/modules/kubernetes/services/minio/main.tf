resource "random_password" "root_password" {
  length  = 32
  special = false
}


resource "helm_release" "minio" {
  name      = "${var.name}-minio"
  namespace = var.namespace

  repository = "https://raw.githubusercontent.com/bitnami/charts/defb094c658024e4aa8245622dab202874880cbc/bitnami"
  chart      = "minio"
  # last release that was Apache-2.0
  version = "6.7.4"

  set {
    name  = "accessKey.password"
    value = "admin"
  }

  set {
    name  = "secretKey.password"
    value = random_password.root_password.result
  }

  set {
    name  = "defaultBuckets"
    value = join(" ", var.buckets)
  }

  set {
    name  = "persistence.size"
    value = var.storage
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
        repository = "bitnamilegacy/minio"
        tag        = "2021.4.22"
      }
      nodeSelector = {
        "${var.node-group.key}" = var.node-group.value
      }
    })
  ], var.overrides)
}
