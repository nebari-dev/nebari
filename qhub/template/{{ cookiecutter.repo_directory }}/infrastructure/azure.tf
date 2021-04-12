provider "azure" {
  versions {}
}


module "registry" {
  source   = "github.com/quansight/qhub-terraform-modules//modules/azure/registry?ref={{ cookiecutter.terraform_modules.rev }}"
  name     = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
  location = "{{ cookiecutter.azure.region }}"
  resource_group_name = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
}


module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/azure/kubernetes?ref={{ cookiecutter.terraform_modules.rev }}"

  name                = local.cluster_name
  environment         = var.environment
  location            = var.region
  resource_group_name = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
  kubernetes_version  = "{{ cookiecutter.azure.kubernetes_version }}"

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
