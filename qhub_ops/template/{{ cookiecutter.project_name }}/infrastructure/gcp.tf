provider "google" {
  credentials = file("account.json")
  project     = "{{ cookiecutter.google_cloud_platform.project }}"
  region      = "{{ cookiecutter.google_cloud_platform.region }}"
  zone        = "{{ cookiecutter.google_cloud_platform.zone }}"
}


module "registry-jupyterhub" {
  source = "github.com/quansight/qhub-terraform-modules//modules/gcp/registry"
}


module "kubernetes" {
  source = "github.com/quansight/qhub-terraform-modules//modules/gcp/kubernetes"

  name     = local.cluster_name
  location = var.region

  availability_zones = var.availability_zones

  additional_node_group_roles = [
    "roles/storage.objectViewer"
  ]

  additional_node_group_oauth_scopes = [
    "https://www.googleapis.com/auth/devstorage.read_only"
  ]

  node_groups = [
    {
      name          = "general"
      instance_type = "{{ cookiecutter.google_cloud_platform.node_groups.general.instance }}"
      min_size      = {{ cookiecutter.google_cloud_platform.node_groups.general.min_nodes }}
      max_size      = {{ cookiecutter.google_cloud_platform.node_groups.general.max_nodes }}
    },
    {
      name          = "user"
      instance_type = "{{ cookiecutter.google_cloud_platform.node_groups.user.instance }}"
      min_size      = {{ cookiecutter.google_cloud_platform.node_groups.user.min_nodes }}
      max_size      = {{ cookiecutter.google_cloud_platform.node_groups.user.max_nodes }}
    },
    {
      name          = "worker"
      instance_type = "{{ cookiecutter.google_cloud_platform.node_groups.worker.instance }}"
      min_size      = {{ cookiecutter.google_cloud_platform.node_groups.worker.min_nodes }}
      max_size      = {{ cookiecutter.google_cloud_platform.node_groups.worker.max_nodes }}
    }
  ]
}
