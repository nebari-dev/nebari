terraform {
  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}

provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "kubectl" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

resource "kubernetes_namespace" "metallb" {
  count = var.metallb_ip_min != "" && var.metallb_ip_max != "" && var.metallb_enabled ? 1 : 0
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
  count = var.metallb_ip_min != "" && var.metallb_ip_max != "" && var.metallb_enabled ? 1 : 0
  yaml_body = yamlencode({
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata = {
      namespace = kubernetes_namespace.metallb.0.metadata.0.name
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
