output "ingress_jupyter" {
  description = "<domain> ingress endpoint"
  value       = module.kubernetes-ingress.endpoint
}
