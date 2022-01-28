output "credentials" {
  description = "Credentials required for connecting to kubernets cluster"
  sensitive = true
  value = {
    endpoint = "https://${google_container_cluster.main.endpoint}"
    token    = data.google_client_config.main.access_token
    cluster_ca_certificate = base64decode(
    google_container_cluster.main.master_auth.0.cluster_ca_certificate)
  }
}

output "kubeconfig" {
  description = "Kubeconfig for connecting to kubernetes cluster"
  sensitive = true
  value = templatefile("${path.module}/templates/kubeconfig.yaml", {
    cluster_name    = google_container_cluster.main.name
    endpoint        = google_container_cluster.main.endpoint
    cluster_ca      = google_container_cluster.main.master_auth.0.cluster_ca_certificate
    client_cert     = google_container_cluster.main.master_auth.0.client_certificate
    client_key      = google_container_cluster.main.master_auth.0.client_key
  })
}
