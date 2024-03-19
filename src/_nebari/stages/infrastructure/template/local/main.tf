terraform {
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.4.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.16.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.7.0"
    }
  }
}

provider "kind" {

}

provider "docker" {

}

provider "kubernetes" {
  host                   = kind_cluster.default.endpoint
  cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
  client_key             = kind_cluster.default.client_key
  client_certificate     = kind_cluster.default.client_certificate
}

provider "kubectl" {
  load_config_file       = false
  host                   = kind_cluster.default.endpoint
  cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
  client_key             = kind_cluster.default.client_key
  client_certificate     = kind_cluster.default.client_certificate
}

resource "kind_cluster" "default" {
  name           = "test-cluster"
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role  = "general"
      image = "kindest/node:v1.29.2"
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
            "${local.metallb_ip_min}-${local.metallb_ip_max}"
          ]
        }]
      })
    }
  })

  depends_on = [kubectl_manifest.metallb]
}

data "docker_network" "kind" {
  name = "kind"

  depends_on = [kind_cluster.default]
}

locals {
  metallb_ip_min = cidrhost([
    for network in data.docker_network.kind.ipam_config : network if network.gateway != ""
  ][0].subnet, 356)

  metallb_ip_max = cidrhost([
    for network in data.docker_network.kind.ipam_config : network if network.gateway != ""
  ][0].subnet, 406)
}
