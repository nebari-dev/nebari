resource "kubernetes_service_account" "main" {
  metadata {
    name      = "${var.name}-traefik-ingress"
    namespace = var.namespace
  }
}


resource "kubernetes_cluster_role" "main" {
  metadata {
    name = "${var.name}-traefik-ingress"
  }

  rule {
    api_groups = [""]
    resources  = ["services", "endpoints", "secrets"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["extensions", "networking.k8s.io"]
    resources  = ["ingresses", "ingressclasses"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["extensions"]
    resources  = ["ingresses/status"]
    verbs      = ["update"]
  }

  rule {
    api_groups = ["traefik.containo.us"]
    resources  = ["ingressroutes", "ingressroutetcps", "ingressrouteudps", "middlewares", "tlsoptions", "tlsstores", "traefikservices", "serverstransports"]
    verbs      = ["get", "list", "watch"]
  }
}


resource "kubernetes_cluster_role_binding" "main" {
  metadata {
    name = "${var.name}-traefik-ingress"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.main.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.main.metadata.0.name
    namespace = var.namespace
  }
}


resource "kubernetes_service" "main" {
  wait_for_load_balancer = true

  metadata {
    name      = "${var.name}-traefik-ingress"
    namespace = var.namespace
  }

  spec {
    selector = {
      "app.kubernetes.io/component" = "traefik-ingress"
    }

    port {
      name        = "http"
      protocol    = "TCP"
      port        = 80
      target_port = 80
    }

    port {
      name        = "https"
      protocol    = "TCP"
      port        = 443
      target_port = 443
    }

    port {
      name        = "ssh"
      protocol    = "TCP"
      port        = 8022
      target_port = 8022
    }

    port {
      name        = "sftp"
      protocol    = "TCP"
      port        = 8023
      target_port = 8023
    }

    port {
      name        = "tcp"
      protocol    = "TCP"
      port        = 8786
      target_port = 8786
    }

    type = "LoadBalancer"
  }
}

resource "kubernetes_service" "traefik_internal" {
  wait_for_load_balancer = true

  metadata {
    name      = "${var.name}-traefik-internal"
    namespace = var.namespace
    annotations = {
      "prometheus.io/scrape" = "true"
      "prometheus.io/path"   = "/metrics"
      "prometheus.io/port"   = 9000
    }
    labels = {
      "app.kubernetes.io/component" = "traefik-internal-service"
      "app.kubernetes.io/part-of"   = "traefik-ingress"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/component" = "traefik-ingress"
    }

    port {
      name        = "http"
      protocol    = "TCP"
      port        = 9000
      target_port = 9000
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_deployment" "main" {
  metadata {
    name      = "${var.name}-traefik-ingress"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/component" = "traefik-ingress"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/component" = "traefik-ingress"
        }
      }

      spec {
        service_account_name             = kubernetes_service_account.main.metadata.0.name
        termination_grace_period_seconds = 60

        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = var.node-group.key
                  operator = "In"
                  values   = [var.node-group.value]
                }
              }
            }
          }
        }

        container {
          image = "${var.traefik-image.image}:${var.traefik-image.tag}"
          name  = var.name

          security_context {
            capabilities {
              drop = ["ALL"]
              add  = ["NET_BIND_SERVICE"]
            }
          }

          args = concat([
            # Do not send usage stats
            "--global.checknewversion=false",
            "--global.sendanonymoususage=false",
            # allow access to the dashboard directly through the port
            # TODO: eventually needs to be tied into traefik middle
            # security possibly using jupyterhub auth this is not a
            # security risk at the moment since this port is not
            # externally accessible
            "--api.insecure=true",
            "--api.dashboard=true",
            "--ping=true",
            # Start the Traefik Kubernetes Ingress Controller
            "--providers.kubernetesingress=true",
            "--providers.kubernetesingress.namespaces=${var.namespace}",
            "--providers.kubernetesingress.ingressclass=traefik",
            # Start the Traefik Kubernetes CRD Controller Provider
            "--providers.kubernetescrd",
            "--providers.kubernetescrd.namespaces=${var.namespace}",
            "--providers.kubernetescrd.throttleduration=2s",
            "--providers.kubernetescrd.allowcrossnamespace=false",
            # Define two entrypoint ports, and setup a redirect from HTTP to HTTPS.
            "--entryPoints.web.address=:80",
            "--entryPoints.websecure.address=:443",
            "--entrypoints.ssh.address=:8022",
            "--entrypoints.sftp.address=:8023",
            "--entryPoints.tcp.address=:8786",
            "--entryPoints.traefik.address=:9000",
            "--entrypoints.web.http.redirections.entryPoint.to=websecure",
            "--entrypoints.web.http.redirections.entryPoint.scheme=https",
            # Enable Prometheus Monitoring of Traefik
            "--metrics.prometheus=true",
            # Enable debug logging. Useful to work out why something might not be
            # working. Fetch logs of the pod.
            "--log.level=${var.loglevel}",
            ], var.enable-certificates ? [
            "--certificatesresolvers.default.acme.tlschallenge",
            "--certificatesresolvers.default.acme.email=${var.acme-email}",
            "--certificatesresolvers.default.acme.storage=acme.json",
            "--certificatesresolvers.default.acme.caserver=${var.acme-server}",
          ] : [])

          port {
            name           = "http"
            container_port = 80
          }

          port {
            name           = "https"
            container_port = 443
          }

          port {
            name           = "ssh"
            container_port = 8022
          }

          port {
            name           = "sftp"
            container_port = 8023
          }

          port {
            name           = "tcp"
            container_port = 8786
          }

          port {
            name           = "traefik"
            container_port = 9000
          }

          liveness_probe {
            http_get {
              path = "/ping"
              port = "traefik"
            }

            initial_delay_seconds = 10
            timeout_seconds       = 2
            period_seconds        = 10
            failure_threshold     = 3
            success_threshold     = 1
          }

          readiness_probe {
            http_get {
              path = "/ping"
              port = "traefik"
            }

            initial_delay_seconds = 10
            timeout_seconds       = 2
            period_seconds        = 10
            failure_threshold     = 1
            success_threshold     = 1
          }
        }
      }
    }
  }
}
