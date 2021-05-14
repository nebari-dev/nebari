resource "kubernetes_manifest" "main" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1beta1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "daskclusters.gateway.dask.org"
    }
    spec = {
      group   = "gateway.dask.org"
      version = "v1alpha1"
      names = {
        kind     = "DaskCluster"
        listKind = "DaskClusterList"
        plural   = "daskclusters"
        singular = "daskcluster"
      }
      scope = "Namespaced"

      subresources = {
        status = {}
      }
    }
  }
}
