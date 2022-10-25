output "load_balancer_address" {
  description = "traefik load balancer address"
  value       = module.kubernetes-ingress.endpoint
}
