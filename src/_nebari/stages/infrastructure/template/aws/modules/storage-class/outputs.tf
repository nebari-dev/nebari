

output "efs_storage_class_name" {
  description = "EFS storage class name"
  value       = kubernetes_storage_class.efs_storage_class.metadata[0].name
}

output "efs_storage_class_retain_name" {
  description = "EFS storage class name"
  value       = kubernetes_storage_class.efs_storage_class_retain.metadata[0].name
}
