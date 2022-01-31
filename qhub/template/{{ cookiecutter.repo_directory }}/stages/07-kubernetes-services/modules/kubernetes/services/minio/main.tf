resource "random_password" "root_password" {
  length  = 32
  special = false
}


resource "helm_release" "minio" {
  name      = "${var.name}-minio"
  namespace = var.namespace

  repository = "https://charts.bitnami.com/bitnami"
  chart      = "minio"
  version    = "9.2.4"

  set {
    name  = "auth.rootUser"
    value = "admin"
  }

  set {
    name  = "auth.rootPassword"
    value = random_password.root_password.result
  }

  set {
    name  = "defaultBuckets"
    value = join(" ", var.buckets)
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
