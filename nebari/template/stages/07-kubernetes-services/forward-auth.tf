module "forwardauth" {
  source = "./modules/kubernetes/forwardauth"

  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id

  node-group = var.node_groups.general
}
