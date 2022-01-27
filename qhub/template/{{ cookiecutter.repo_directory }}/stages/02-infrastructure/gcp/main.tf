data "google_compute_zones" "gcpzones" {
  region = var.region
}


module "registry-jupyterhub" {
  source = "./modules/gcp/registry"
}


module "kubernetes" {
  source = "./modules/gcp/kubernetes"

  name     = local.cluster_name
  location = var.region

  availability_zones = length(var.availability_zones) >= 1 ? var.availability_zones : [data.google_compute_zones.gcpzones.names[0]]

  additional_node_group_roles = [
    "roles/storage.objectViewer",
    "roles/storage.admin"
  ]

  additional_node_group_oauth_scopes = [
    "https://www.googleapis.com/auth/cloud-platform"
  ]

  node_groups = [
    for name, config in node_groups: {
      name          = name
      instance_type = config.instance
      min_size      = config.min_nodes
      max_size      = config.max_nodes
      labels        = config.labels
      preemptible   = config.preemptible
      guest_accelerators = config.guest_accelerators
    }
  ]
}
