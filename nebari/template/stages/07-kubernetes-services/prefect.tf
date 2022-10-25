# ======================= VARIABLES ======================
variable "prefect-enabled" {
  description = "Prefect enabled or disabled"
  type        = bool
}

variable "prefect-image" {
  description = "Prefect image"
  type        = string
}

variable "prefect-token" {
  description = "Prefect token"
  type        = string
}

variable "prefect-overrides" {
  description = "Prefect token"
  type        = map(any)
}


# ====================== RESOURCES =======================
module "prefect" {
  count = var.prefect-enabled ? 1 : 0

  source = "./modules/kubernetes/services/prefect"

  namespace            = var.environment
  jupyterhub_api_token = module.jupyterhub.services.prefect.api_token
  prefect_token        = var.prefect-token
  image                = var.prefect-image
  overrides            = [yamlencode(var.prefect-overrides)]
}
