provider "kind" {}

module "kubernetes" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/kind/kubernetes?ref={{ cookiecutter.terraform_modules.rev }}"
  name   = local.cluster_name
}
