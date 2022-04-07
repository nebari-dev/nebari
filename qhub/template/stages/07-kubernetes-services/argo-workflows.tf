# ======================= VARIABLES ======================
variable "argo-workflows-enabled" {
  description = "Argo Workflows enabled"
  type        = bool
  default     = true
}

# ====================== RESOURCES =======================
module "argo-workflows" {
  count = var.argo-workflows-enabled ? 1 : 0

  source       = "./modules/kubernetes/services/argo-workflows"
  namespace    = var.environment
  external-url = var.endpoint
  # realm_id     = var.realm_id

  # node-group = var.node_groups.general
}
