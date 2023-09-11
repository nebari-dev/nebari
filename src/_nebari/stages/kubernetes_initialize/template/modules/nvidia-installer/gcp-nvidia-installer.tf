# source https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#installing_drivers
resource "kubernetes_daemonset" "gcp_nvidia_installer" {
  count = var.gpu_enabled && (var.cloud_provider == "gcp") ? 1 : 0

  metadata {
    name      = "nvidia-driver-installer"
    namespace = "kube-system"
    labels = {
      "k8s-app" = "nvidia-driver-installer"
    }
  }

  spec {
    selector {
      match_labels = {
        "k8s-app" = "nvidia-driver-installer"
      }
    }

    template {
      metadata {
        labels = {
          name      = "nvidia-driver-installer"
          "k8s-app" = "nvidia-driver-installer"
        }
      }

      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = "cloud.google.com/gke-accelerator"
                  operator = "Exists"
                }
              }
            }
          }
        }
        toleration {
          operator = "Exists"
        }
        host_network = true
        host_pid     = true
        volume {
          name = "dev"
          host_path {
            path = "/dev"
          }
        }
        volume {
          name = "vulkan-icd-mount"
          host_path {
            path = "/home/kubernetes/bin/nvidia/vulkan/icd.d"
          }
        }
        volume {
          name = "nvidia-install-dir-host"
          host_path {
            path = "/home/kubernetes/bin/nvidia"
          }
        }
        volume {
          name = "root-mount"
          host_path {
            path = "/"
          }
        }
        volume {
          name = "cos-tools"
          host_path {
            path = "/var/lib/cos-tools"
          }
        }
        init_container {
          image   = "cos-nvidia-installer:fixed"
          name    = "nvidia-driver-installer"
          command = ["/cos-gpu-installer", "install", "--version=latest"]
          resources {
            requests = {
              cpu = 0.15
            }
          }
          security_context {
            privileged = true
          }
          env {
            name  = "NVIDIA_INSTALL_DIR_HOST"
            value = "/home/kubernetes/bin/nvidia"
          }
          env {
            name  = "NVIDIA_INSTALL_DIR_CONTAINER"
            value = "/usr/local/nvidia"
          }
          env {
            name  = "VULKAN_ICD_DIR_HOST"
            value = "/home/kubernetes/bin/nvidia/vulkan/icd.d"
          }
          env {
            name  = "VULKAN_ICD_DIR_CONTAINER"
            value = "/etc/vulkan/icd.d"
          }
          env {
            name  = "ROOT_MOUNT_DIR"
            value = "/root"
          }
          env {
            name  = "COS_TOOLS_DIR_HOST"
            value = "/var/lib/cos-tools"
          }
          env {
            name  = "COS_TOOLS_DIR_CONTAINER"
            value = "/build/cos-tools"
          }
          volume_mount {
            name       = "nvidia-install-dir-host"
            mount_path = "/usr/local/nvidia"
          }
          volume_mount {
            name       = "vulkan-icd-mount"
            mount_path = "/etc/vulkan/icd.d"
          }
          volume_mount {
            name       = "dev"
            mount_path = "/dev"
          }
          volume_mount {
            name       = "root-mount"
            mount_path = "/root"
          }
          volume_mount {
            name       = "cos-tools"
            mount_path = "/build/cos-tools"
          }
        }
        container {
          image = "gcr.io/google-containers/pause:2.0"
          name  = "pause"
        }
      }
    }

    strategy {
      type = "RollingUpdate"
    }
  }
}
