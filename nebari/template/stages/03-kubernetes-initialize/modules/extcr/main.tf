resource "kubernetes_secret" "customer_extcr_key" {
  metadata {
    name      = "customer-extcr-key"
    namespace = var.namespace
  }

  data = {
    "access-key-id"     = var.access_key_id
    "secret-access-key" = var.secret_access_key
    "extcr-account"     = var.extcr_account
    "extcr-region"      = var.extcr_region
  }
}

resource "kubernetes_manifest" "role_extcr_cred_updater" {
  manifest = {
    "apiVersion" = "rbac.authorization.k8s.io/v1"
    "kind"       = "Role"
    "metadata" = {
      "name"      = "extcr-cred-updater"
      "namespace" = var.namespace
    }
    "rules" = [
      {
        "apiGroups" = [
          "",
        ]
        "resources" = [
          "secrets",
        ]
        "verbs" = [
          "get",
          "create",
          "delete",
        ]
      },
      {
        "apiGroups" = [
          "",
        ]
        "resources" = [
          "serviceaccounts",
        ]
        "verbs" = [
          "get",
          "patch",
        ]
      },
    ]
  }
}

resource "kubernetes_manifest" "serviceaccount_extcr_cred_updater" {
  manifest = {
    "apiVersion" = "v1"
    "kind"       = "ServiceAccount"
    "metadata" = {
      "name"      = "extcr-cred-updater"
      "namespace" = var.namespace
    }
  }
}

resource "kubernetes_manifest" "rolebinding_extcr_cred_updater" {
  manifest = {
    "apiVersion" = "rbac.authorization.k8s.io/v1"
    "kind"       = "RoleBinding"
    "metadata" = {
      "name"      = "extcr-cred-updater"
      "namespace" = var.namespace
    }
    "roleRef" = {
      "apiGroup" = "rbac.authorization.k8s.io"
      "kind"     = "Role"
      "name"     = "extcr-cred-updater"
    }
    "subjects" = [
      {
        "kind" = "ServiceAccount"
        "name" = "extcr-cred-updater"
      },
    ]
  }
}

resource "kubernetes_manifest" "job_extcr_cred_updater" {
  manifest = {
    "apiVersion" = "batch/v1"
    "kind"       = "Job"
    "metadata" = {
      "name"      = "extcr-cred-updater"
      "namespace" = var.namespace
    }
    "spec" = {
      "backoffLimit" = 4
      "template" = {
        "spec" = {
          "containers" = [
            {
              "command" = [
                "/bin/sh",
                "-c",
                <<-EOT
                DOCKER_REGISTRY_SERVER=https://$${AWS_ACCOUNT}.dkr.ecr.$${AWS_REGION}.amazonaws.com
                DOCKER_USER=AWS
                DOCKER_PASSWORD=`aws ecr get-login --region $${AWS_REGION} --registry-ids $${AWS_ACCOUNT} | cut -d' ' -f6`
                kubectl delete secret extcrcreds || true
                kubectl create secret docker-registry extcrcreds \
                --docker-server=$DOCKER_REGISTRY_SERVER \
                --docker-username=$DOCKER_USER \
                --docker-password=$DOCKER_PASSWORD \
                --docker-email=no@email.local
                kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"extcrcreds"}]}'

                EOT
                ,
              ]
              "env" = [
                {
                  "name" = "AWS_ACCESS_KEY_ID"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "access-key-id"
                      "name" = "customer-extcr-key"
                    }
                  }
                },
                {
                  "name" = "AWS_SECRET_ACCESS_KEY"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "secret-access-key"
                      "name" = "customer-extcr-key"
                    }
                  }
                },
                {
                  "name" = "AWS_ACCOUNT"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "extcr-account"
                      "name" = "customer-extcr-key"
                    }
                  }
                },
                {
                  "name" = "AWS_REGION"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "extcr-region"
                      "name" = "customer-extcr-key"
                    }
                  }
                },
              ]
              "image" = "xynova/aws-kubectl"
              "name"  = "kubectl"
            },
          ]
          "restartPolicy"                 = "Never"
          "serviceAccountName"            = "extcr-cred-updater"
          "terminationGracePeriodSeconds" = 0
        }
      }
    }
  }
}

resource "kubernetes_manifest" "cronjob_extcr_cred_updater" {
  manifest = {
    "apiVersion" = "batch/v1"
    "kind"       = "CronJob"
    "metadata" = {
      "name"      = "extcr-cred-updater"
      "namespace" = var.namespace
    }
    "spec" = {
      "failedJobsHistoryLimit" = 1
      "jobTemplate" = {
        "spec" = {
          "backoffLimit" = 4
          "template" = {
            "spec" = {
              "containers" = [
                {
                  "command" = [
                    "/bin/sh",
                    "-c",
                    <<-EOT
                    DOCKER_REGISTRY_SERVER=https://$${AWS_ACCOUNT}.dkr.ecr.$${AWS_REGION}.amazonaws.com
                    DOCKER_USER=AWS
                    DOCKER_PASSWORD=`aws ecr get-login --region $${AWS_REGION} --registry-ids $${AWS_ACCOUNT} | cut -d' ' -f6`
                    kubectl delete secret extcrcreds || true
                    kubectl create secret docker-registry extcrcreds \
                    --docker-server=$DOCKER_REGISTRY_SERVER \
                    --docker-username=$DOCKER_USER \
                    --docker-password=$DOCKER_PASSWORD \
                    --docker-email=no@email.local
                    kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"extcrcreds"}]}'
                    EOT
                    ,
                  ]
                  "env" = [
                    {
                      "name" = "AWS_ACCESS_KEY_ID"
                      "valueFrom" = {
                        "secretKeyRef" = {
                          "key"  = "access-key-id"
                          "name" = "customer-extcr-key"
                        }
                      }
                    },
                    {
                      "name" = "AWS_SECRET_ACCESS_KEY"
                      "valueFrom" = {
                        "secretKeyRef" = {
                          "key"  = "secret-access-key"
                          "name" = "customer-extcr-key"
                        }
                      }
                    },
                    {
                      "name" = "AWS_ACCOUNT"
                      "valueFrom" = {
                        "secretKeyRef" = {
                          "key"  = "extcr-account"
                          "name" = "customer-extcr-key"
                        }
                      }
                    },
                    {
                      "name" = "AWS_REGION"
                      "valueFrom" = {
                        "secretKeyRef" = {
                          "key"  = "extcr-region"
                          "name" = "customer-extcr-key"
                        }
                      }
                    },
                  ]
                  "image" = "xynova/aws-kubectl"
                  "name"  = "kubectl"
                },
              ]
              "restartPolicy"                 = "Never"
              "serviceAccountName"            = "extcr-cred-updater"
              "terminationGracePeriodSeconds" = 0
            }
          }
        }
      }
      "schedule"                   = "* */8 * * *"
      "successfulJobsHistoryLimit" = 1
    }
  }
}
