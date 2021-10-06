locals {
  clearml_webserver_subdomain  = "app.clearml"
  clearml_fileserver_subdomain = "files.clearml"
  clearml_apiserver_subdomain  = "api.clearml"
  clearml-prefix               = "clearml-clearml-server-cloud-ready"
  clearml_webserver            = "${local.clearml-prefix}-webserver"
  clearml_fileserver           = "${local.clearml-prefix}-fileserver"
  clearml_apiserver            = "${local.clearml-prefix}-apiserver"

  forward_auth_middleware = "traefik-forward-auth"
  clearml_middleware = var.enable-forward-auth ? [
    {
      name      = local.forward_auth_middleware
      namespace = var.namespace
    }
  ] : []
}

resource "kubernetes_manifest" "clearml-app" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "clearml-app"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${local.clearml_webserver_subdomain}.${var.external-url}`)"
          middlewares = local.clearml_middleware
          services = [
            {
              name      = local.clearml_webserver
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}

resource "kubernetes_manifest" "clearml-files" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "clearml-files"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${local.clearml_fileserver_subdomain}.${var.external-url}`)"
          middlewares = local.clearml_middleware
          services = [
            {
              name      = local.clearml_fileserver
              port      = 8081
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}

resource "kubernetes_manifest" "clearml-api" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "clearml-api"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind        = "Rule"
          match       = "Host(`${local.clearml_apiserver_subdomain}.${var.external-url}`)"
          middlewares = local.clearml_middleware
          services = [
            {
              name      = local.clearml_apiserver
              port      = 8008
              namespace = var.namespace
            }
          ]
        }
      ]
      tls = var.tls
    }
  }
}
