# ======================= VARIABLES ======================
variable "argo-workflows-overrides" {
  description = "Argo Workflows helm chart overrides"
  type        = list(string)
}

variable "nebari-workflow-controller" {
  description = "Nebari Workflow Controller enabled"
  type        = bool
}


variable "keycloak-read-only-user-credentials" {
  description = "Keycloak password for nebari-bot"
  type        = map(string)
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
  keycloak-read-only-user-credentials = var.keycloak-read-only-user-credentials
  workflow-controller-image-tag       = var.workflow-controller-image-tag
  nebari-workflow-controller          = var.nebari-workflow-controller
}
