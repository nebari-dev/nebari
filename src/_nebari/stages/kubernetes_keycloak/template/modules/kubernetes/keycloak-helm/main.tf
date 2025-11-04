# Standalone PostgreSQL database for Keycloak
# Deployed separately to allow safe upgrade from keycloak to keycloakx chart
resource "helm_release" "keycloak_postgresql" {
  name       = "keycloak-postgres-standalone"
  namespace  = var.namespace
  repository = "oci://registry-1.docker.io/bitnamicharts"
  chart      = "postgresql"
  version    = "18.0.15"

  values = [
    jsonencode({
      primary = {
        nodeSelector = {
          "${var.node_group.key}" = var.node_group.value
        }
      }
      auth = {
        username = "keycloak"
        password = "keycloak"
        database = "keycloak"
      }
    })
  ]
}

resource "helm_release" "keycloak" {
  name      = "keycloak"
  namespace = var.namespace

  repository = "https://codecentric.github.io/helm-charts"
  chart      = "keycloakx"
  version    = "7.1.3"

  depends_on = [
    helm_release.keycloak_postgresql
  ]

  values = concat([
    # https://github.com/codecentric/helm-charts/blob/keycloak-15.0.2/charts/keycloak/values.yaml
    file("${path.module}/values.yaml"),
    jsonencode({
      nodeSelector = {
        "${var.node_group.key}" = var.node_group.value
      }

      customThemes = var.themes
    })
  ], var.overrides)

  set_sensitive {
    name  = "nebari_bot_password"
    value = var.nebari-bot-password
  }

  set {
    name  = "initial_root_password"
    value = var.initial_root_password
  }

  set {
    name  = "external_url"
    value = var.external-url
  }
}

# Track changes to values.yaml
resource "terraform_data" "values_hash" {
  input = filesha256("${path.module}/values.yaml")
}


resource "kubernetes_manifest" "keycloak-http" {
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
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/auth`) "
          services = [
            {
              name      = "keycloak-keycloakx-http"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
