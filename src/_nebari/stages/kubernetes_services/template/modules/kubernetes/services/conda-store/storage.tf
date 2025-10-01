module "minio" {
  source = "../minio"

  name         = "nebari-conda-store"
  namespace    = var.namespace
  external-url = var.external-url

  node-group = var.node-group

  storage = var.minio_capacity

  buckets = [
    "conda-store"
  ]
}


module "postgresql" {
  source = "../postgresql"

  name      = "nebari-conda-store"
  namespace = var.namespace

  node-group = var.node-group

  database = "conda-store"
}


module "redis" {
  source = "../redis"

  name      = "nebari-conda-store"
  namespace = var.namespace

  node-group = var.node-group

  # TODO: Remove hardcoded image values after Helm chart update
  # This is a workaround due to bitnami charts deprecation
  # See: https://github.com/bitnami/charts/issues/35164
  # https://github.com/nebari-dev/nebari/issues/3139
  overrides = [
    jsonencode({
      image = {
        registry   = "docker.io"
        repository = "bitnamilegacy/redis"
        tag        = "7.0.4-debian-11-r4"
      }
    })
  ]
}
