resource "kubernetes_namespace" "main" {
  metadata {
    labels = merge({}, var.labels)

    name = var.namespace
  }
}


resource "kubernetes_secret" "main" {
  count = length(var.secrets)

  metadata {
    name      = var.secrets[count.index].name
    namespace = var.namespace
    labels    = merge({}, var.labels)
  }

  data = var.secrets[count.index].data

  type = "Opaque"
}
