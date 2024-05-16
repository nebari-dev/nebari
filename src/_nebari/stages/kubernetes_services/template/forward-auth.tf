module "forwardauth" {
  source = "./modules/kubernetes/forwardauth"

  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id

  node-group = var.node_groups.general
}

output "forward-auth-middleware" {
  description = "middleware name for use with forward auth"
  value       = module.forwardauth.forward-auth-middleware
}

output "forward-auth-service" {
  description = "middleware name for use with forward auth"
  value       = module.forwardauth.forward-auth-service
}
