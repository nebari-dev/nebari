variable "monitoring-enabled" {
  description = "Prometheus and Grafana monitoring enabled"
  type        = bool
  default     = true
}

module "monitoring" {
  count = var.monitoring-enabled ? 1 : 0

  source       = "./modules/kubernetes/services/monitoring"
  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id

  node-group = var.node_groups.general
}
