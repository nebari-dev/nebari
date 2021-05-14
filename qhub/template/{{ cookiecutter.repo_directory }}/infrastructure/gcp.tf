provider "google" {
  project = "{{ cookiecutter.google_cloud_platform.project }}"
  region  = "{{ cookiecutter.google_cloud_platform.region }}"
  zone    = "{{ cookiecutter.google_cloud_platform.zone }}"
}


module "registry-jupyterhub" {
  source = "./modules/gcp/registry"
}


module "kubernetes" {
  source = "./modules/gcp/kubernetes"

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
{%- if nodegroup_config.preemptible is defined %}
      preemptible   = {{ "true" if nodegroup_config.preemptible else "false" }}
{%- endif %}
{%- if nodegroup_config.guest_accelerators is defined %}
      guest_accelerators = [
{%- for accelerator in nodegroup_config.guest_accelerators %}
        {
          type  = "{{ accelerator.name }}"
          count = {{ accelerator.count }}
        },
{%- endfor %}
      ]
{%- endif %}
    },
{% endfor %}
  ]
}
