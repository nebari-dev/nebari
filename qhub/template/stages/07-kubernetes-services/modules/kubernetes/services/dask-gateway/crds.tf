resource "kubernetes_manifest" "main" {
  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "daskclusters.gateway.dask.org"
    }
    spec = {
      group = "gateway.dask.org"
      names = {
        kind     = "DaskCluster"
        listKind = "DaskClusterList"
        plural   = "daskclusters"
        singular = "daskcluster"
      }
      scope = "Namespaced"
      versions = [{
        name    = "v1alpha1"
        served  = true
        storage = true
        subresources = {
          status = {}
        }

        # NOTE: While we define a schema, it is a dummy schema that doesn't
        #       validate anything. We just have it to comply with the schema of
        #       a CustomResourceDefinition that requires it.
        #
        #       A decision has been made to not implement an actual schema at
        #       this point in time due to the additional maintenance work it
        #       would require.
        #
        #       Reference: https://github.com/dask/dask-gateway/issues/434
        #
        schema = {
          openAPIV3Schema = {
            type = "object"
            # FIXME: Make this an actual schema instead of this dummy schema that
            #        is a workaround to meet the requirement of having a schema.
            x-kubernetes-preserve-unknown-fields = true
          }
        }
      }]
    }
  }
}
