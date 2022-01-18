module "minio" {
  source = "../minio"

  name = "qhub-conda-store"
  namespace = var.namespace
  tls =  local.tls
  external-url = var.external-url
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
