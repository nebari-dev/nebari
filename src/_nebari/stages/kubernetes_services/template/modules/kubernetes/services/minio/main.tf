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

  # TODO: Remove hardcoded image.registry, image.repository, and image.tag values after Helm chart update
  # This is a workaround due to bitnami charts deprecation
  # See: https://github.com/bitnami/charts/issues/35164
  # See: https://github.com/nebari-dev/nebari/issues/3120
  set {
    name  = "image.registry"
    value = "docker.io"
  }

  set {
    name  = "image.repository"
    value = "bitnamilegacy/minio"
  }

  set {
    name  = "image.tag"
    value = "2021.4.22"
  }

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      nodeSelector = {
        "${var.node-group.key}" = var.node-group.value
      }
    })
  ], var.overrides)
}
