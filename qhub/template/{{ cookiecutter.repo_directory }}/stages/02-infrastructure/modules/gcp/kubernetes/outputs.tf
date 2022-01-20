output "credentials" {
  description = "Credentials required for connecting to kubernets cluster"
  value = {
    endpoint = "https://${google_container_cluster.main.endpoint}"
    token    = data.google_client_config.main.access_token
    cluster_ca_certificate = base64decode(
    google_container_cluster.main.master_auth.0.cluster_ca_certificate)
  }
}
