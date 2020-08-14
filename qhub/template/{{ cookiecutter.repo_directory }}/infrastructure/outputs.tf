output "ingress_jupyter" {
  description = "jupyter.<domain> ingress endpoint"
  value       = module.kubernetes-ingress.endpoint
}
