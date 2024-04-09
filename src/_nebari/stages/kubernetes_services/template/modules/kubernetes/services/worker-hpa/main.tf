resource "kubernetes_manifest" "triggerauthenticator" {
  manifest = {
    apiVersion = "keda.sh/v1alpha1"
    kind       = "TriggerAuthentication"

    metadata = {
      name      = "trigger-auth-postgres"
      namespace = var.namespace
    }

    spec = {
      secretTargetRef = [
        {
          name      = "nebari-conda-store-postgresql"
          parameter = "password"
          key       = "postgresql-password"
        }
      ]
    }
  }
}

resource "kubernetes_manifest" "scaledobject" {
  manifest = {
    apiVersion = "keda.sh/v1alpha1"
    kind       = "ScaledObject"

    metadata = {
      name      = "scaled-conda-worker"
      namespace = var.namespace
    }

    spec = {
      scaleTargetRef = {
        kind = "Deployment"
        name = "nebari-conda-store-worker"
      }
      minReplicaCount: 1 # Default: 0
      pollingInterval: 5 # Default:  30 seconds
      cooldownPeriod: 60 # Default: 300 seconds
      triggers = [
        {
          type = "postgresql"
          metadata = {
            query            = "SELECT COUNT(*) FROM build WHERE status IN ('QUEUED', 'BUILDING');"
            targetQueryValue = "1"
            host             = "nebari-conda-store-postgresql"
            userName         = "postgres"
            port             = "5432"
            dbName           = "conda-store"
            sslmode          = "disable"
          }
          authenticationRef = {
            name = "trigger-auth-postgres"
          }
        }
      ]
    }
  }
}
