
resource "kubernetes_storage_class" "efs_storage_class" {
  metadata {
    name = "efs-dynamic"
  }

  storage_provisioner = "efs.csi.aws.com"
  reclaim_policy      = "Delete"

  parameters = {
    provisioningMode = "efs-ap"
    fileSystemId     = var.shared_fs_id
    directoryPerms   = "777"
    gid              = 100
    uid              = 1000

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
    fileSystemId     = var.shared_fs_id
    directoryPerms   = "777"
    gid              = 100
    uid              = 1000
  }

  mount_options = ["tls"]
}
