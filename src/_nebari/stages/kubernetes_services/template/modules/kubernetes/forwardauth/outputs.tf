output "forward-auth-middleware" {
  description = "middleware name for use with forward auth"
  value = {
    name = kubernetes_manifest.forwardauth-middleware.manifest.metadata.name
  }
}

output "forward-auth-service" {
  description = "middleware name for use with forward auth"
  value = {
    name = kubernetes_service.forwardauth-service.metadata.0.name
  }
}
