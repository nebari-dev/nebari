locals {
  node_group_service_account_roles = concat(var.additional_node_group_roles, [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer"
  ])

  node_group_oauth_scopes = concat(var.additional_node_group_oauth_scopes, [
    "https://www.googleapis.com/auth/logging.write",
    "https://www.googleapis.com/auth/monitoring"
  ])

  merged_node_groups = [for node_group in var.node_groups : merge(var.node_group_defaults, node_group)]

}
