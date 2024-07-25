output "persistent_volume_claim" {
  description = "Name of persistent volume claim"
  value = {
    pvc = {
      name = kubernetes_persistent_volume_claim.main.metadata.0.name
      id   = kubernetes_persistent_volume_claim.main.metadata.0.uid
    }
    namespace = var.namespace
    kind      = "persistentvolumeclaim"
  }
}
