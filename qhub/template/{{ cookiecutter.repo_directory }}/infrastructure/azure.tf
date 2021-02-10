provider "azure" {
  versions{}
}


module "registry" {
  source = "github.com/quansight/qhub-terraform-modules//modules/azure/registry?ref=azure"
  name   = "{{ cookiecutter.project_name }}"
  location   = "{{ cookiecutter.project_name }}"
}


module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/azure/kubernetes?ref=azure"

  name = local.cluster_name

  location             = var.region
  kubernetes_version = "{{ cookiecutter.azure.kubernetes_version }}"

  node_groups = [
{% for nodegroup, nodegroup_config in cookiecutter.azure.node_groups.items() %}
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
