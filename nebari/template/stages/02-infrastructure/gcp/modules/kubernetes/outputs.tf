output "credentials" {
  description = "Credentials required for connecting to kubernets cluster"
  sensitive   = true
  value = {
    endpoint = "https://${google_container_cluster.main.endpoint}"
    token    = data.google_client_config.main.access_token
    cluster_ca_certificate = base64decode(
    google_container_cluster.main.master_auth.0.cluster_ca_certificate)
  }
}


# https://github.com/terraform-google-modules/terraform-google-kubernetes-engine/blob/9172b3eaeeb806caca29aa1e3e83e58a26df57b1/modules/auth/main.tf
data "google_client_config" "provider" {}

output "kubeconfig" {
  description = "Kubeconfig for connecting to kubernetes cluster"
  sensitive   = true
  value = templatefile("${path.module}/templates/kubeconfig.yaml", {
    context                = google_container_cluster.main.name
    cluster_ca_certificate = google_container_cluster.main.master_auth[0].cluster_ca_certificate
    endpoint               = google_container_cluster.main.endpoint
    token                  = data.google_client_config.provider.access_token
  })
}
