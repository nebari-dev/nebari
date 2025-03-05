terraform {
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}

resource "kubernetes_namespace" "metallb" {
  metadata {
    name = "metallb-system"
  }
}

data "kubectl_path_documents" "metallb" {
  pattern = "${path.module}/metallb.yaml"
}

resource "kubectl_manifest" "metallb" {
  for_each   = toset(data.kubectl_path_documents.metallb.documents)
  yaml_body  = each.value
  wait       = true
  depends_on = [kubernetes_namespace.metallb]
}

resource "kubectl_manifest" "load-balancer" {
  yaml_body = yamlencode({
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata = {
      namespace = kubernetes_namespace.metallb.metadata.0.name
      name      = "config"
    }
    data = {
      config = yamlencode({
        address-pools = [{
          name     = "default"
          protocol = "layer2"
          addresses = [
            "${var.metallb_ip_min}-${var.metallb_ip_max}"
          ]
        }]
      })
    }
  })

  depends_on = [kubectl_manifest.metallb]
}
