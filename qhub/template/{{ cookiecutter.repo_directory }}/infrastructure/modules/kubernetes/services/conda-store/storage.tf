module "minio" {
  source = "../minio"

  name = "qhub-conda-store"
  namespace = var.namespace
  tls =  module.qhub.tls
  buckets = [
    "conda-store"
  ]
}


module "postgresql" {
  source = "../postgresql"

  name = "qhub-conda-store"
  namespace = var.namespace

  database = "conda-store"
}
