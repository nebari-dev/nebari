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
      # singleNamespace = true # Restrict Argo to operate only in a single namespace (the namespace of the Helm release)

      # controller = {
      #   metricsConfig = {
      #     enabled = true # enable prometheus
      #   }
      #   workflowNamespaces = [
      #     "${var.namespace}"
      #   ]
      #   nodeSelector = {
      #     "${var.node-group.key}" = var.node-group.value
      #   }
      # }

      # server = {
      #   # `sso` for OIDC/OAuth
      #   extraArgs = ["--auth-mode=sso", "--auth-mode=client", "--insecure-skip-verify"]
      #   # to enable TLS, `secure = true`
      #   secure   = false
      #   baseHref = "/${local.argo-workflows-prefix}/"

      #   sso = {
      #     insecureSkipVerify = true
      #     issuer             = "https://${var.external-url}/auth/realms/${var.realm_id}"
      #     clientId = {
      #       name = "argo-server-sso"
      #       key  = "argo-oidc-client-id"
      #     }
      #     clientSecret = {
      #       name = "argo-server-sso"
      #       key  = "argo-oidc-client-secret"
      #     }
      #     # The OIDC redirect URL. Should be in the form <argo-root-url>/oauth2/callback.
      #     redirectUrl = "https://${var.external-url}/${local.argo-workflows-prefix}/oauth2/callback"
      #     rbac = {
      #       # https://argoproj.github.io/argo-workflows/argo-server-sso/#sso-rbac
      #       enabled         = true
      #       secretWhitelist = []
      #     }
      #     customGroupClaimName = "roles"
      #     scopes               = ["roles"]
      #   }
      #   nodeSelector = {
      #     "${var.node-group.key}" = var.node-group.value
      #   }
      # }

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

  values = concat([
    file("${path.module}/cluster-values.yaml"),

    jsonencode({
      operatorNamespace = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
    })
  ], var.overrides)

  depends_on = [helm_release.rook-ceph]
}

data "kubernetes_storage_class" "rook-ceph-fs-delete-sc" {
  metadata {
    name = "ceph-filesystem" # TODO: Make sure we get this right
  }
}

locals {
  storage-class = data.kubernetes_storage_class.rook-ceph-fs-delete-sc
}

resource "kubernetes_storage_class" "ceph-retain_sc" {
  metadata {
    name = "${data.kubernetes_storage_class.rook-ceph-fs-delete-sc.metadata[0].name}-retain" # "ceph-filesystem-retain"  # TODO: Make sure we get this right
  }
  storage_provisioner    = local.storage-class.storage_provisioner # "rook-ceph.cephfs.csi.ceph.com"
  reclaim_policy         = "Retain"
  volume_binding_mode    = local.storage-class.volume_binding_mode
  allow_volume_expansion = local.storage-class.allow_volume_expansion
  parameters             = local.storage-class.parameters
}
