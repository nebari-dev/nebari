provider "digitalocean" {}

module "kubernetes" {
  source = "./modules/digitalocean/kubernetes"

  name = local.cluster_name

  region             = var.region
  kubernetes_version = "{{ cookiecutter.digital_ocean.kubernetes_version }}"

  node_groups = [
{% for nodegroup, nodegroup_config in cookiecutter.digital_ocean.node_groups.items() %}
    {
      name       = "{{ nodegroup }}"
      auto_scale = true

      size      = "{{ nodegroup_config.instance }}"
      min_nodes = {{ nodegroup_config.min_nodes }}
      max_nodes = {{ nodegroup_config.max_nodes }}
    },
{% endfor %}
  ]
}
