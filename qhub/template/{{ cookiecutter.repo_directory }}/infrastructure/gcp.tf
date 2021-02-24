provider "google" {
  project = "{{ cookiecutter.google_cloud_platform.project }}"
  region  = "{{ cookiecutter.google_cloud_platform.region }}"
  zone    = "{{ cookiecutter.google_cloud_platform.zone }}"
}


module "registry-jupyterhub" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/gcp/registry?ref={{ cookiecutter.terraform_modules.rev }}"
}


module "kubernetes" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/gcp/kubernetes?ref={{ cookiecutter.terraform_modules.rev }}"

  name     = local.cluster_name
  location = var.region

  availability_zones = var.availability_zones

  additional_node_group_roles = [
    "roles/storage.objectViewer",
    "roles/storage.admin"
  ]

  additional_node_group_oauth_scopes = [
    "https://www.googleapis.com/auth/cloud-platform"
  ]

  node_groups = [
{% for nodegroup, nodegroup_config in cookiecutter.google_cloud_platform.node_groups.items() %}
    {
      name          = "{{ nodegroup }}"
      instance_type = "{{ nodegroup_config.instance }}"
      min_size      = {{ nodegroup_config.min_nodes }}
      max_size      = {{ nodegroup_config.max_nodes }}
      {%- if "preemptible" in nodegroup_config %}
      preemptible   = {{ "true" if nodegroup_config.preemptible else "false" }}
      {%- endif %}
      {%- if nodegroup.guest_accelerators is defined %}
      guest_accelerators = [
        {% for accelerator in nodegroup_config.guest_accelerators %}
        {
          type  = "{{ accelerator.name }}"
          count = {{ accelerator.count }}
        }
        {% endfor %}
      ]
      {%- endif %}
    },
{% endfor %}
  ]
}
