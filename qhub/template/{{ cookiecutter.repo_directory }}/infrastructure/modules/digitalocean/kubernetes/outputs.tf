output "credentials" {
  description = "Credentials needs to connect to kubernetes instance"
  value = {
    endpoint = digitalocean_kubernetes_cluster.main.endpoint
    token    = digitalocean_kubernetes_cluster.main.kube_config[0].token
    cluster_ca_certificate = base64decode(
      digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
    )
  }
}
