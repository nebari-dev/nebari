# ======================= VARIABLES ======================
variable "argo-workflows-enabled" {
  description = "Argo Workflows enabled"
  type        = bool
  default     = true
}

variable "argo-workflows-overrides" {
  description = "Argo Workflows helm chart overrides"
  type        = list(string)
  default     = []
}

variable "keycloak_read_only_user_credentials" {
  description = "Keycloak password for nebari-bot"
  type        = map(string)
  default     = {}
}

variable "workflow-controller-image-tag" {
  description = "Image tag for nebari-workflow-controller"
  type        = string
}


# ====================== RESOURCES =======================
module "argo-workflows" {
  count = var.argo-workflows-enabled ? 1 : 0

  source       = "./modules/kubernetes/services/argo-workflows"
  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id

  node-group                          = var.node_groups.general
  overrides                           = var.argo-workflows-overrides
  keycloak_read_only_user_credentials = var.keycloak_read_only_user_credentials
  workflow-controller-image-tag       = var.workflow-controller-image-tag
}
