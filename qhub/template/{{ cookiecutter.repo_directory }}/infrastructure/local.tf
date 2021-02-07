provider "kind" {}

module "kubernetes" {
  source = "github.com/brl0/qhub-terraform-modules//modules/local/kubernetes?ref=local_kind"
  name   = local.cluster_name
}
