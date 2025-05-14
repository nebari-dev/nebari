provider "kubernetes" {
  host                   = var.endpoint
  token                  = var.token
  cluster_ca_certificate = var.cluster_ca_certificate
}

resource "kubernetes_storage_class" "efs_storage_class" {
  metadata {
    name = "efs-dynamic"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner = "efs.csi.aws.com"
  reclaim_policy      = "Delete"

  parameters = {
    provisioningMode = "efs-ap"
    fileSystemId     = var.efs_filesystem_id
    directoryPerms   = "777"
    gid              = 100
    uid              = 1001

  }

  mount_options = ["tls"]
}

resource "kubernetes_storage_class" "efs_storage_class_retain" {
  metadata {
    name = "efs-dynamic-retain"
  }

  storage_provisioner = "efs.csi.aws.com"
  reclaim_policy      = "Retain"

  parameters = {
    provisioningMode = "efs-ap"
    fileSystemId     = var.efs_filesystem_id
    directoryPerms   = "777"
    gid              = 100
    uid              = 1001
  }

  mount_options = ["tls"]
}
