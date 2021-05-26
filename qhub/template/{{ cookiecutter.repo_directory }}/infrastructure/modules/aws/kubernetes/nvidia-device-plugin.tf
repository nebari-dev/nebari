resource "kubernetes_daemonset" "nvidia_installer" {
  count = length(local.gpu_node_group_names) == 0 ? 0 : 1
  metadata {
    name      = "nvidia-device-plugin-daemonset-1.12"
    namespace = "kube-system"
  }

  spec {
    selector {
      match_labels = {
        name = "nvidia-device-plugin-ds"
      }
    }

    template {
      metadata {
        labels = {
          name = "nvidia-device-plugin-ds"
        }
      }

      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = "eks.amazonaws.com/nodegroup"
                  operator = "In"
                  values   = local.gpu_node_group_names
                }
              }
            }
          }
        }

        volume {
          name = "device-plugin"

          host_path {
            path = "/var/lib/kubelet/device-plugins"
          }
        }

        container {
          name  = "nvidia-device-plugin-ctr"
          image = "nvidia/k8s-device-plugin:1.11"

          volume_mount {
            name       = "device-plugin"
            mount_path = "/var/lib/kubelet/device-plugins"
          }

          security_context {
            capabilities {
              drop = ["ALL"]
            }
          }
        }

        toleration {
          key      = "CriticalAddonsOnly"
          operator = "Exists"
        }

        toleration {
          key      = "nvidia.com/gpu"
          operator = "Exists"
          effect   = "NoSchedule"
        }
      }
    }

    strategy {
      type = "RollingUpdate"
    }
  }
}

