provider "digitalocean" {}


module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/digitalocean/kubernetes"

  name = local.cluster_name

  region             = var.region
  kubernetes_version = "{{ cookiecutter.digital_ocean.kubernetes_version }}"

  node_groups = [
    {
      name = "general"

      auto_scale = true

      size      = "{{ cookiecutter.digital_ocean.node_groups.general.instance }}"
      min_nodes = {{ cookiecutter.digital_ocean.node_groups.general.min_nodes }}
      max_nodes = {{ cookiecutter.digital_ocean.node_groups.general.max_nodes }}
    },
    {
      name = "user"

      auto_scale = true

      size      = "{{ cookiecutter.digital_ocean.node_groups.user.instance }}"
      min_nodes = {{ cookiecutter.digital_ocean.node_groups.user.min_nodes }}
      max_nodes = {{ cookiecutter.digital_ocean.node_groups.user.max_nodes }}
    },
    {
      name = "worker"

      auto_scale = true

      size      = "{{ cookiecutter.digital_ocean.node_groups.worker.instance }}"
      min_nodes = {{ cookiecutter.digital_ocean.node_groups.worker.min_nodes }}
      max_nodes = {{ cookiecutter.digital_ocean.node_groups.worker.max_nodes }}
    }
  ]
}
