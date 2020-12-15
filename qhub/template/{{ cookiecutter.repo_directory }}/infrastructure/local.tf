provider "kind" {}

module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/local/kubernetes?ref=brl0_local"
  name   = local.cluster_name
}
