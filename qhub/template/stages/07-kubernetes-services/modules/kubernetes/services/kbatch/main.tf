resource "helm_release" "kbatch" {
  name       = "kbatch"
  namespace  = var.namespace
  repository = "https://kbatch-dev.github.io/helm-chart"
  chart      = "kbatch-proxy"
  version    = local.kbatch_version

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      app = {
        jupyterhub_api_token = var.jupyterhub_api_token
        jupyterhub_api_url   = "https://${var.external-url}/hub/api/"
        extra_env = {
          KBATCH_PREFIX = ""
          KBATCH_JOB_EXTRA_ENV = jsonencode({
            DASK_GATEWAY__AUTH__TYPE              = "jupyterhub"
            DASK_GATEWAY__CLUSTER__OPTIONS__IMAGE = "${var.dask-worker-image.name}:${var.dask-worker-image.tag}"
            DASK_GATEWAY__ADDRESS                 = "${var.dask-gateway-address}"
            DASK_GATEWAY__PROXY_ADDRESS           = "${var.dask-gateway-proxy-address}"
          })
        }
      }
      image = {
        tag = local.kbatch_version
      }
    })
  ])

  set_sensitive {
    name  = "jupyterHubToken"
    value = var.jupyterhub_api_token
  }

  set {
    name  = "kbatchImage"
    value = var.image
  }

  set {
    name  = "namespace"
    value = var.namespace
  }

}

resource "kubernetes_cluster_role" "kbatch" {
  metadata {
    name = "${var.name}-kbatch"
  }

  rule {
    api_groups = ["", "batch"]
    resources  = ["*"]
    verbs      = ["get", "watch", "list", "patch", "create", "delete"]
  }
}


resource "kubernetes_cluster_role_binding" "kbatch" {
  metadata {
    name = "${var.name}-kbatch"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.kbatch.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = local.kbatch_service_account_name
    namespace = var.namespace
    api_group = ""
  }
}
