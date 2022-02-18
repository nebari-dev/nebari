module "minio" {
  source = "../minio"

  name = "qhub-conda-store"
  namespace = var.namespace
  external-url = var.external-url

  node-group = var.node-group

  buckets = [
    "conda-store"
  ]
}


module "postgresql" {
  source = "../postgresql"

  name = "qhub-conda-store"
  namespace = var.namespace

  node-group = var.node-group

  database = "conda-store"
}
