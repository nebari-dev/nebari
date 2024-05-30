module "forwardauth" {
  source = "./modules/kubernetes/forwardauth"

  namespace    = var.environment
  external-url = var.endpoint
  realm_id     = var.realm_id

  node-group                  = var.node_groups.general
  forwardauth_middleware_name = var.forwardauth_middleware_name
  cert_secret_name            = var.cert_secret_name
}

variable "forwardauth_middleware_name" {
  description = "Name of the traefik forward auth middleware"
  type        = string
}

variable "cert_secret_name" {
  description = "Name of the secret containing the certificate"
  type        = string
}

output "forward-auth-middleware" {
  description = "middleware name for use with forward auth"
  value       = module.forwardauth.forward-auth-middleware
}

output "forward-auth-service" {
  description = "middleware name for use with forward auth"
  value       = module.forwardauth.forward-auth-service
}
