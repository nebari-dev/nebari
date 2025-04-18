locals {
  default_cert = [
    "--entrypoints.websecure.http.tls.certResolver=default",
    "--entrypoints.minio.http.tls.certResolver=default",
  ]
  certificate-challenge = {
    dns = [
      "--certificatesresolvers.letsencrypt.acme.dnschallenge=true",
      # Only cloudflare is supported at the moment for DNS challenge
      # TODO: add support for other DNS providers
      "--certificatesresolvers.letsencrypt.acme.dnschallenge.provider=cloudflare"
    ]
    tls = [
      "--certificatesresolvers.letsencrypt.acme.tlschallenge",
    ]
  }
  # for dns challenge, we need to set the cloudflare env vars
  cloudflare_env_vars = var.acme-challenge-type == "dns" ? [
    {
      name  = "CLOUDFLARE_DNS_API_TOKEN"
      value = var.cloudflare-dns-api-token
    }
  ] : []
  certificate-settings = {
    lets-encrypt = concat([
      "--entrypoints.websecure.http.tls.certResolver=letsencrypt",
      "--entrypoints.minio.http.tls.certResolver=letsencrypt",
      "--certificatesresolvers.letsencrypt.acme.email=${var.acme-email}",
      "--certificatesresolvers.letsencrypt.acme.storage=/mnt/acme-certificates/acme.json",
      "--certificatesresolvers.letsencrypt.acme.caserver=${var.acme-server}",
      ], local.certificate-challenge[var.acme-challenge-type]
    )
    self-signed = local.default_cert
    existing    = local.default_cert
    disabled    = []
  }
  add-certificate = local.certificate-settings[var.certificate-service]
}


resource "kubernetes_service_account" "main" {
  metadata {
    name      = "${var.name}-traefik-ingress"
    namespace = var.namespace
  }
}

resource "kubernetes_persistent_volume_claim" "traefik_certs_pvc" {
  metadata {
    name      = "traefik-ingress-certs"
    namespace = var.namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
  }
  wait_until_bound = false
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
    resources  = ["ingressroutes", "ingressroutetcps", "ingressrouteudps", "middlewares", "middlewaretcps", "tlsoptions", "tlsstores", "traefikservices", "serverstransports"]
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
    name        = "${var.name}-traefik-ingress"
    namespace   = var.namespace
    annotations = var.load-balancer-annotations
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
      name        = "minio"
      protocol    = "TCP"
      port        = 9080
      target_port = 9080
    }

    port {
      name        = "tcp"
      protocol    = "TCP"
      port        = 8786
      target_port = 8786
    }

    type             = "LoadBalancer"
    load_balancer_ip = var.load-balancer-ip
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

          dynamic "env" {
            for_each = local.cloudflare_env_vars
            content {
              name  = env.value.name
              value = env.value.value
            }
          }

          volume_mount {
            mount_path = "/mnt/acme-certificates"
            name       = "acme-certificates"
          }
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
            # Define the entrypoint port for Minio
            "--entryPoints.minio.address=:9080",
            # Redirect http -> https
            "--entrypoints.web.http.redirections.entryPoint.to=websecure",
            "--entrypoints.web.http.redirections.entryPoint.scheme=https",
            # Enable Prometheus Monitoring of Traefik
            "--metrics.prometheus=true",
            # Enable debug logging. Useful to work out why something might not be
            # working. Fetch logs of the pod.
            "--log.level=${var.loglevel}",
            ],
            local.add-certificate,
            var.additional-arguments,
          )

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

          port {
            name           = "minio"
            container_port = 9080
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
        volume {
          name = "acme-certificates"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.traefik_certs_pvc.metadata.0.name
          }
        }
      }
    }
  }
}


resource "kubernetes_manifest" "tlsstore_default" {
  count = var.certificate-secret-name != null ? 1 : 0
  manifest = {
    "apiVersion" = "traefik.containo.us/v1alpha1"
    "kind"       = "TLSStore"
    "metadata" = {
      "name"      = "default"
      "namespace" = var.namespace
    }
    "spec" = {
      "defaultCertificate" = {
        "secretName" = var.certificate-secret-name
      }
    }
  }
}
