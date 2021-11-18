locals {
  tls = (var.certificate-secret-name != "") ? ({
    secretName = var.certificate-secret-name
    }) : ({
    certResolver = "default"
  })
}
