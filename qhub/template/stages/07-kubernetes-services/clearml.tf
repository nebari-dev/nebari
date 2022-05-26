# ======================= VARIABLES ======================
variable "clearml-enabled" {
  description = "Clearml enabled or disabled"
  type        = bool
  default     = false
}

variable "clearml-enable-forwardauth" {
  description = "Clearml enabled or disabled forward authentication"
  type        = bool
  default     = false
}


variable "clearml-overrides" {
  description = "Clearml helm chart overrides"
  type        = list(string)
  default     = []
}


# ====================== RESOURCES =======================
module "clearml" {
  count = var.clearml-enabled ? 1 : 0

  source = "./modules/kubernetes/services/clearml"

  namespace    = var.environment
  external-url = var.endpoint

  overrides = var.clearml-overrides

  enable-forward-auth = var.clearml-enable-forwardauth
}
