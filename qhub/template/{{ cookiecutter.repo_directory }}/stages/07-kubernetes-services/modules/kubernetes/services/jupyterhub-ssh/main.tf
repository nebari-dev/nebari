resource "kubernetes_manifest" "jupyterhub-ssh-ingress" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRouteTCP"
    metadata = {
      name      = "jupyterhub-ssh-ingress"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["ssh"]
      routes = [
        {
          match = "HostSNI(`*`)"
          services = [
            {
              name = kubernetes_service.jupyterhub-ssh.metadata.0.name
              port = 8022
            }
          ]
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "jupyterhub-sftp-ingress" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRouteTCP"
    metadata = {
      name      = "jupyterhub-sftp-ingress"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["sftp"]
      routes = [
        {
          match = "HostSNI(`*`)"
          services = [
            {
              name = kubernetes_service.jupyterhub-sftp.metadata.0.name
              port = 8023
            }
          ]
        }
      ]
    }
  }
}
