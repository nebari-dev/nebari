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
}
