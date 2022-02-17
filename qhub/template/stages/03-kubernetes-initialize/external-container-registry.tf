module "external-container-reg" {
  count = var.external_container_reg.enabled ? 1 : 0

  source = "./modules/extcr"

  namespace         = var.environment
  access_key_id     = var.external_container_reg.access_key_id
  secret_access_key = var.external_container_reg.secret_access_key
  extcr_account     = var.external_container_reg.extcr_account
  extcr_region      = var.external_container_reg.extcr_region

  depends_on = [module.kubernetes-initialization]
}
