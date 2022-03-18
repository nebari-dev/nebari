resource "kubernetes_secret" "qhub_yaml_secret" {
  metadata {
    name      = "qhub-config-yaml"
    namespace = var.environment
  }

  data = {
    "qhub-config.yaml" = yamlencode(var.qhub_config_yaml)
  }
}
