resource "kubernetes_secret" "nebari_yaml_secret" {
  metadata {
    name      = "nebari-config-yaml"
    namespace = var.environment
  }

  data = {
    "nebari-config.yaml" = yamlencode(var.nebari_config_yaml)
  }
}
