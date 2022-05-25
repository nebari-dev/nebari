resource "digitalocean_kubernetes_cluster" "main" {
  name   = var.name
  region = var.region

  # Grab the latest from `doctl kubernetes options versions`
  version = var.kubernetes_version

  node_pool {
    name = local.master_node_group.name
    # List available regions `doctl kubernetes options sizes`
    size       = lookup(local.master_node_group, "size", "s-1vcpu-2gb")
    node_count = lookup(local.master_node_group, "node_count", 1)
  }

  tags = var.tags
}

resource "digitalocean_kubernetes_node_pool" "main" {
  count = length(local.additional_node_groups)

  cluster_id = digitalocean_kubernetes_cluster.main.id

  name = local.additional_node_groups[count.index].name
  size = lookup(local.additional_node_groups[count.index], "size", "s-1vcpu-2gb")

  auto_scale = lookup(local.additional_node_groups[count.index], "auto_scale", true)
  min_nodes  = lookup(local.additional_node_groups[count.index], "min_nodes", 1)
  max_nodes  = lookup(local.additional_node_groups[count.index], "max_nodes", 1)

  labels = {
    "qhub.dev/node_group" : local.additional_node_groups[count.index].name
  }

  tags = var.tags
}
