resource "kubernetes_manifest" "jupyterhub-middleware-addprefix" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-jupyterhub-add-prefix"
      namespace = var.namespace
    }
    spec = {
      addPrefix = {
        prefix = "/hub"
      }
    }
  }
}

resource "kubernetes_manifest" "jupyterhub-proxy-add-slash" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-jupyterhub-proxy-add-slash"
      namespace = var.namespace
    }
    spec = {
      redirectRegex = {
        regex       = "^https://${var.external-url}/user/([^/]+)/proxy/(\\d+)$"
        replacement = "https://${var.external-url}/user/$${1}/proxy/$${2}/"
        permanent   = true
      }
    }
  }
}

resource "kubernetes_manifest" "jupyterhub-proxy-jupyter-gallery" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-jupyterhub-proxy-jupyter-gallery"
      namespace = var.namespace
    }
    spec = {
      replacePathRegex = {
        regex       = "^/user/([^/]+)/jupyterlab-gallery(/?[^/]+)$"
        replacement = "/user/$${1}/proxy/${var.jupyterlab-gallery-sidecar-port}/jupyterlab-gallery$${2}"
      }
    }
  }
}
