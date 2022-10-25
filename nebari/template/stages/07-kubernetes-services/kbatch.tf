# ======================= VARIABLES ======================
variable "kbatch-enabled" {
  description = "kbatch enabled or disabled"
  type        = bool
}


# ====================== RESOURCES =======================
module "kbatch" {
  count = var.kbatch-enabled ? 1 : 0

  source = "./modules/kubernetes/services/kbatch"

  namespace    = var.environment
  external-url = var.endpoint

  jupyterhub_api_token = module.jupyterhub.services.kbatch.api_token
  node-group           = var.node_groups.user

  dask-gateway-address       = module.dask-gateway.config.gateway.address
  dask-gateway-proxy-address = module.dask-gateway.config.gateway.proxy_address
  dask-worker-image          = var.dask-worker-image
}
