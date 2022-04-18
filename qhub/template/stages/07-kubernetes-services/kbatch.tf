# ======================= VARIABLES ======================
variable "kbatch-enabled" {
  description = "kbatch enabled or disabled"
  type = bool
}

variable "kbatch-image" {
  description = "kbatch image"
  type = string
}

# variable "kbatch-overrides" {
#   description = ""
#   type = map
# }


# ====================== RESOURCES =======================
module "kbatch" {
  count = var.kbatch-enabled ? 1 : 0

  source = "./modules/kubernetes/services/kbatch"

  namespace            = var.environment
  jupyterhub_api_token = module.jupyterhub.services.kbatch.api_token
  image                = var.kbatch-image
  admin                = true
  url                  = "http://kbatch-proxy.${var.environment}.svc.cluster.local"
#   overrides            = [yamlencode(var.kbatch-overrides)]
}
