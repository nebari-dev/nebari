output "endpoint" {
  description = "Endpoint dns name of conda-store nfs server"
  value       = "${kubernetes_service.nfs.metadata.0.name}.${var.namespace}.svc.cluster.local"
}

output "endpoint_ip" {
  description = "IP Address of conda-store nfs server"
  value       = kubernetes_service.nfs.spec.0.cluster_ip
}
