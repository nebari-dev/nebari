resource "helm_release" "rook-ceph-cluster" {
  name          = "rook-ceph-cluster"
  namespace     = var.namespace
  repository    = "https://charts.rook.io/release"
  chart         = "rook-ceph-cluster"
  version       = "v1.14.7"
  wait          = true
  wait_for_jobs = true

  values = concat([
    templatefile("${path.module}/cluster-values.yaml.tftpl",
      {
        "storageClassName"    = var.storage_class_name,
        "node_group"          = var.node_group,
        "storage_capacity_Gi" = var.ceph_storage_capacity,
    }),
    jsonencode({
      operatorNamespace = var.operator_namespace,
    })
  ], var.overrides)
}

locals {
  storage-class           = data.kubernetes_storage_class.rook-ceph-fs-delete-sc
  storage-class-base-name = "ceph-filesystem"
}

data "kubernetes_storage_class" "rook-ceph-fs-delete-sc" {
  metadata {
    name = local.storage-class-base-name # TODO: Make sure we get this right
  }
  depends_on = [helm_release.rook-ceph-cluster]
}

resource "kubernetes_storage_class" "ceph-retain-sc" {
  metadata {
    name = "${local.storage-class-base-name}-retain" # "ceph-filesystem-retain"  # TODO: Make sure we get this right
  }
  storage_provisioner    = local.storage-class.storage_provisioner # "rook-ceph.cephfs.csi.ceph.com"
  reclaim_policy         = "Retain"
  volume_binding_mode    = local.storage-class.volume_binding_mode
  allow_volume_expansion = local.storage-class.allow_volume_expansion
  parameters             = local.storage-class.parameters

  depends_on = [data.kubernetes_storage_class.rook-ceph-fs-delete-sc]
}

# This is necessary on GKE to completely create a ceph cluster
resource "kubernetes_resource_quota" "rook_critical_pods" {
  metadata {
    name      = "rook-critical-pods"
    namespace = var.namespace
    labels = {
      "addonmanager.kubernetes.io/mode" = "Reconcile"
    }
  }

  spec {
    hard = {
      "pods" = "1G"
    }

    scope_selector {
      match_expression {
        operator   = "In"
        scope_name = "PriorityClass"
        values     = ["system-node-critical", "system-cluster-critical"]
      }
    }
  }
  # depends_on = [helm_release.rook-ceph]
}
