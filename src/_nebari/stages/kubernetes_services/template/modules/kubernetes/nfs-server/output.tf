output "endpoint" {
  description = "Endpoint dns name of nfs server"
  value       = "${var.name}-nfs.${var.namespace}.svc.cluster.local"
}

output "endpoint_ip" {
  description = "IP Address of nfs server"
  value       = kubernetes_service.main.spec.0.cluster_ip
}
