provider "azurerm" {
  features {}
}


module "registry" {
  source              = "./modules/azure/registry"
  name                = "{{ cookiecutter.project_name }}{{ cookiecutter.namespace }}"
  location            = "{{ cookiecutter.azure.region }}"
  resource_group_name = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
}


module "kubernetes" {
  source = "./modules/azure/kubernetes"

  name                     = local.cluster_name
  environment              = var.environment
  location                 = var.region
  resource_group_name      = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
  node_resource_group_name = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-node-resource-group"
  kubernetes_version       = "{{ cookiecutter.azure.kubernetes_version }}"

  node_groups = [
{% for nodegroup, nodegroup_config in cookiecutter.azure.node_groups.items() %}
    {
      name          = "{{ nodegroup }}"
      auto_scale    = true
      instance_type = "{{ nodegroup_config.instance }}"
      min_size      = {{ nodegroup_config.min_nodes }}
      max_size      = {{ nodegroup_config.max_nodes }}
    },
{% endfor %}
  ]
}
