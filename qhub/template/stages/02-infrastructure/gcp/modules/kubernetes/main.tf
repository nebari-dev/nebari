data "google_client_config" "main" {
}

resource "google_container_cluster" "main" {
  name     = var.name
  location = var.location

  node_locations = var.availability_zones

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  master_auth {
    client_certificate_config {
      issue_client_certificate = true
    }
  }

  networking_mode = var.networking_mode
  network         = var.network
  subnetwork      = var.subnetwork

  dynamic "ip_allocation_policy" {
    for_each = var.ip_allocation_policy == null ? [] : [1]
    content {
      cluster_secondary_range_name  = var.ip_allocation_policy.cluster_secondary_range_name
      services_secondary_range_name = var.ip_allocation_policy.services_secondary_range_name
      cluster_ipv4_cidr_block       = var.ip_allocation_policy.cluster_ipv4_cidr_block
      services_ipv4_cidr_block      = var.ip_allocation_policy.services_ipv4_cidr_block
    }
  }

  dynamic "master_authorized_networks_config" {
    for_each = var.master_authorized_networks_config == null ? [] : [1]
    content {
      cidr_blocks {
        cidr_block   = var.master_authorized_networks_config.cidr_blocks.cidr_block
        display_name = var.master_authorized_networks_config.cidr_blocks.display_name
      }
    }
  }

  dynamic "private_cluster_config" {
    for_each = var.private_cluster_config == null ? [] : [1]
    content {
      enable_private_nodes    = var.private_cluster_config.enable_private_nodes
      enable_private_endpoint = var.private_cluster_config.enable_private_endpoint
      master_ipv4_cidr_block  = var.private_cluster_config.master_ipv4_cidr_block
    }
  }


  lifecycle {
    ignore_changes = [
      node_locations
    ]
  }
}

resource "google_container_node_pool" "main" {
  count = length(local.merged_node_groups)

  name     = local.merged_node_groups[count.index].name
  location = var.location
  cluster  = google_container_cluster.main.name

  initial_node_count = local.merged_node_groups[count.index].min_size

  autoscaling {
    min_node_count = local.merged_node_groups[count.index].min_size
    max_node_count = local.merged_node_groups[count.index].max_size
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = local.merged_node_groups[count.index].preemptible
    machine_type = local.merged_node_groups[count.index].instance_type

    service_account = google_service_account.main.email

    oauth_scopes = local.node_group_oauth_scopes

    metadata = {
      disable-legacy-endpoints = "true"
    }
    labels = local.merged_node_groups[count.index].labels
    dynamic "guest_accelerator" {
      for_each = local.merged_node_groups[count.index].guest_accelerators

      content {
        type  = guest_accelerator.value.name
        count = guest_accelerator.value.count
      }
    }
  }
}
