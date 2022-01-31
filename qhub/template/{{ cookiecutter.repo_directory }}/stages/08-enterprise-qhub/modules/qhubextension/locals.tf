locals {
  tls = (var.certificate-secret-name != "") ? ({
    secretName = var.certificate-secret-name
    }) : ({
    certResolver = "default"
  })

  middlewares = (var.private) ? ([{
    name      = "traefik-forward-auth"
    namespace = var.namespace
  }]) : ([])
}
