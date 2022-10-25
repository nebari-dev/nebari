data "google_compute_zones" "gcpzones" {
  region = var.region
}


module "registry-jupyterhub" {
  source = "./modules/registry"
}


module "kubernetes" {
  source = "./modules/kubernetes"

  name       = "${var.name}-${var.environment}"
  location   = var.region
  project_id = var.project_id

  availability_zones = length(var.availability_zones) >= 1 ? var.availability_zones : [data.google_compute_zones.gcpzones.names[0]]

  additional_node_group_roles = [
    "roles/storage.objectViewer",
    "roles/storage.admin"
  ]

  additional_node_group_oauth_scopes = [
    "https://www.googleapis.com/auth/cloud-platform"
  ]

  node_groups                       = var.node_groups
  network                           = var.network
  subnetwork                        = var.subnetwork
  ip_allocation_policy              = var.ip_allocation_policy
  master_authorized_networks_config = var.master_authorized_networks_config
  private_cluster_config            = var.private_cluster_config
}
