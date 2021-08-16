resource "kubernetes_namespace" "keycloak" {
  metadata {
    name = "keycloak"
  }
}

resource "helm_release" "keycloak" {
  name      = "keycloak"
  namespace = "keycloak"

  repository = "https://codecentric.github.io/helm-charts"
  chart      = "keycloak"
  version    = "14.0.1"

  values = concat([
    file("${path.module}/values.yaml"),
  ], var.overrides)

  set {
    name  = "ingress.rules[0].host"
    value = var.external-url
  }
}

resource "kubernetes_manifest" "keycloak-http" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "keycloak-http"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${var.external-url}`) && PathPrefix(`/auth`) "
          services = [
            {
              name      = "keycloak-headless-external"
              # Really not sure why 8080 works here
              port      = 8080
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}

resource "kubernetes_service" "keycloak-headless-external" {
  metadata {
    name      = "keycloak-headless-external"
    namespace = var.namespace
  }

  spec {
    type = "ExternalName"
    external_name = "keycloak-headless.keycloak.svc.cluster.local"

    port {
      name        = "http"
      protocol    = "TCP"
      port        = 80
      target_port = 80
    }
  }
}

# Converted from https://github.com/keycloak/keycloak-operator/blob/master/deploy/operator.yaml
# using https://github.com/jrhouston/tfk8s
resource "kubernetes_manifest" "deployment_keycloak_operator" {
  provider = kubernetes-alpha

  manifest = {
    "apiVersion" = "apps/v1"
    "kind" = "Deployment"
    "metadata" = {
      "name" = "keycloak-operator"
      "namespace" = "keycloak"
    }
    "spec" = {
      "replicas" = 1
      "selector" = {
        "matchLabels" = {
          "name" = "keycloak-operator"
        }
      }
      "template" = {
        "metadata" = {
          "labels" = {
            "name" = "keycloak-operator"
          }
        }
        "spec" = {
          "containers" = [
            {
              "command" = [
                "keycloak-operator",
              ]
              "env" = [
                {
                  "name" = "WATCH_NAMESPACE"
                  "valueFrom" = {
                    "fieldRef" = {
                      "fieldPath" = "metadata.namespace"
                    }
                  }
                },
                {
                  "name" = "POD_NAME"
                  "valueFrom" = {
                    "fieldRef" = {
                      "fieldPath" = "metadata.name"
                    }
                  }
                },
                {
                  "name" = "OPERATOR_NAME"
                  "value" = "keycloak-operator"
                },
              ]
              "image" = "quay.io/keycloak/keycloak-operator:14.0.0"
              "imagePullPolicy" = "Always"
              "name" = "keycloak-operator"
            },
          ]
          "serviceAccountName" = "keycloak-operator"
        }
      }
    }
  }
}
