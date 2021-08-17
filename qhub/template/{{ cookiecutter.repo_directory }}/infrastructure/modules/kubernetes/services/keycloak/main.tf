terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = "3.3.0"
    }
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

resource "keycloak_realm" "realm-master" {
  provider = keycloak
  
  realm = "providerrealm"

  display_name = "Provider Updated Again2"

  smtp_server {
    host = "smtp.gmail.com"
    from = "email@test.com"

    auth {
      username = "email@test.com"
      password = "<password>"
    }
  }

  depends_on = [helm_release.keycloak]
}
