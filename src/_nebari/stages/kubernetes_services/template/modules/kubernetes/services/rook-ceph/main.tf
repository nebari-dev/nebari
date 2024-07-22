locals {
  # name                  = "rook-ceph"
  # argo-workflows-prefix = "argo"
  # # roles
  # admin     = "argo-admin"
  # developer = "argo-developer"
  # viewer    = "argo-viewer"
}

resource "kubernetes_namespace" "rook-ceph" {
  metadata {
    name = "rook-ceph" # TODO: Make this a variable
  }
}

resource "helm_release" "rook-ceph" {
  name       = "rook-ceph"
  namespace  = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
  repository = "https://charts.rook.io/release"
  chart      = "rook-ceph"
  version    = "v1.14.7"

  values = concat([
    file("${path.module}/operator-values.yaml"),
    jsonencode({
      nodeSelector = {
        "${var.node_group.key}" = var.node_group.value
      },
      monitoring = {
        enabled = false # TODO: Enable monitoring when nebari-config.yaml has it enabled
      },
      csi = {
        enableRbdDriver = false, # necessary to provision block storage, but saves some cpu and memory if not needed
      },
    })
  ], var.overrides)

  depends_on = [kubernetes_namespace.rook-ceph]
}

resource "helm_release" "rook-ceph-cluster" {
  name       = "rook-ceph-cluster"
  namespace  = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
  repository = "https://charts.rook.io/release"
  chart      = "rook-ceph-cluster"
  version    = "v1.14.7"
  wait       = true

  values = concat([
    templatefile("${path.module}/cluster-values.yaml.tftpl",
      {
        "storageClassName"    = var.storage_class_name,
        "node_group"          = var.node_group,
        "storage_capacity_Gi" = var.ceph_storage_capacity,
    }),
    jsonencode({
      operatorNamespace = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
    })
  ], var.overrides)

  depends_on = [helm_release.rook-ceph, kubernetes_resource_quota.rook_critical_pods]
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

# add this resource but in terraform
# apiVersion: v1
# kind: ResourceQuota
# metadata:
#   # annotations:
#   labels:
#     addonmanager.kubernetes.io/mode: Reconcile
#   name: rook-critical-pods
#   namespace: rook-ceph
# spec:
#   hard:
#     pods: 1G
#   scopeSelector:
#     matchExpressions:
#     - operator: In
#       scopeName: PriorityClass
#       values:
#       - system-node-critical
#       - system-cluster-critical

# This is necessary on GKE to completely create a ceph cluster
resource "kubernetes_resource_quota" "rook_critical_pods" {
  metadata {
    name      = "rook-critical-pods"
    namespace = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
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
  depends_on = [helm_release.rook-ceph]
}
