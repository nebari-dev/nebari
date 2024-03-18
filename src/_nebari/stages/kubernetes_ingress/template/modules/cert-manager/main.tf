resource "helm_release" "cert_manager" {
  chart      = "cert-manager"
  repository = "https://charts.jetstack.io"
  name       = "cert-manager"
  namespace  = var.namespace_name
  version    = var.chart_version

  # TODO Add a node selector
  set {
    name  = "installCRDs"
    value = "true"
  }

  values = concat([file("${path.module}/values.yaml")])

}

## TODO: Pick staging on non-dev evns
#resource "kubernetes_manifest" "clusterissuer_letsencrypt_staging" {
#  manifest = {
#    "apiVersion" = "cert-manager.io/v1"
#    "kind" = "ClusterIssuer"
#    "metadata" = {
#      "name" = "letsencrypt-staging"
#    }
#    "spec" = {
#      "acme" = {
#        "email" = "var.cluster_issuer_email"
#        "privateKeySecretRef" = {
#          "name" = "letsencrypt-staging"
#        }
#        "server" = "https://acme-staging-v02.api.letsencrypt.org/directory"
#        "solvers" = [
#          {
#            "http01" = {
#              "ingress" = {
#                "ingressClassName" = "traefik"
#              }
#            }
#          },
#        ]
#      }
#    }
#  }
#}


resource "kubernetes_manifest" "clusterissuer_letsencrypt_production" {
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind" = "ClusterIssuer"
    "metadata" = {
      "name" = "letsencrypt-production"
    }
    "spec" = {
      "acme" = {
        "email" = var.acme-email
        "privateKeySecretRef" = {
          "name" = "letsencrypt-production"
        }
        "server" = var.acme-server
#        "solvers" = [
#          {
#            "http01" = {
#              "ingress" = {
#                "ingressClassName" = "traefik"
#              }
#            }
#          },
#        ]
      }
    }
  }
}



#resource "kubernetes_manifest" "certificate_local_nebari_dev" {
#  manifest = {
#    "apiVersion" = "cert-manager.io/v1"
#    "kind" = "Certificate"
#    "metadata" = {
#      "name" = "local-nebari-dev"
#      "namespace" = "default"
#    }
#    "spec" = {
#      "commonName" = "*.local-nebari-dev"
#      "dnsNames" = [
#        "local-nebari-dev",
#        "*.local-nebari-dev",
#      ]
#      "issuerRef" = {
#        "kind" = "ClusterIssuer"
#        "name" = "letsencrypt-staging"
#      }
#      "secretName" = "local-nebari-dev-staging-tls"
#    }
#  }
#}

resource "kubernetes_manifest" "certificate_local_nebari_dev" {
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind" = "Certificate"
    "metadata" = {
      "name" = "local-nebari.dev"
      "namespace" = var.namespace_name
    }
    "spec" = {
      "commonName" = "*.local-nebari.dev"
      "dnsNames" = [
        "local-nebari.dev",
        "*.local-nebari.dev",
      ]
      "issuerRef" = {
        "kind" = "ClusterIssuer"
        "name" = "letsencrypt-production"
      }
      "secretName" = "local-nebari-dev-tls"
    }
  }
}
