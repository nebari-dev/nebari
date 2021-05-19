output "endpoint" {
  description = "Endpoint dns name of conda-store nfs server"
  value       = "${var.name}-nfs.${var.namespace}.svc.cluster.local"
}

output "endpoint_ip" {
  description = "IP Address of conda-store nfs server"
  value       = kubernetes_service.main.spec.0.cluster_ip
}
