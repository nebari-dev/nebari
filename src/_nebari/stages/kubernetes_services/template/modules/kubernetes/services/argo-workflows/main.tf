locals {
  name                  = "argo-workflows"
  argo-workflows-prefix = "argo"
  # roles
  admin     = "argo-admin"
  developer = "argo-developer"
  viewer    = "argo-viewer"
}

resource "helm_release" "argo-workflows" {
  name       = local.name
  namespace  = var.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  version    = "0.22.9"

  values = concat([
    file("${path.module}/values.yaml"),

    jsonencode({
      singleNamespace = true # Restrict Argo to operate only in a single namespace (the namespace of the Helm release)

      controller = {
        metricsConfig = {
          enabled = true # enable prometheus
        }
        workflowNamespaces = [
          "${var.namespace}"
        ]
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

      server = {
        # `sso` for OIDC/OAuth
        extraArgs = ["--auth-mode=sso", "--auth-mode=client", "--insecure-skip-verify"]
        # to enable TLS, `secure = true`
        secure   = false
        baseHref = "/${local.argo-workflows-prefix}/"

        sso = {
          insecureSkipVerify = true
          issuer             = "https://${var.external-url}/auth/realms/${var.realm_id}"
          clientId = {
            name = "argo-server-sso"
            key  = "argo-oidc-client-id"
          }
          clientSecret = {
            name = "argo-server-sso"
            key  = "argo-oidc-client-secret"
          }
          # The OIDC redirect URL. Should be in the form <argo-root-url>/oauth2/callback.
          redirectUrl = "https://${var.external-url}/${local.argo-workflows-prefix}/oauth2/callback"
          rbac = {
            # https://argoproj.github.io/argo-workflows/argo-server-sso/#sso-rbac
            enabled         = true
            secretWhitelist = []
          }
          customGroupClaimName = "roles"
          scopes               = ["roles"]
        }
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

    })
  ], var.overrides)
}

resource "kubernetes_secret" "argo-oidc-secret" {
  metadata {
    name      = "argo-server-sso"
    namespace = var.namespace
  }
  data = {
    "argo-oidc-client-id"     = module.argo-workflow-openid-client.config.client_id
    "argo-oidc-client-secret" = module.argo-workflow-openid-client.config.client_secret
  }
}

module "argo-workflow-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "argo-server-sso"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["${local.admin}"]
    "developer" = ["${local.developer}"]
    "analyst"   = ["${local.viewer}"]
  }

  callback-url-paths = [
    "https://${var.external-url}/${local.argo-workflows-prefix}/oauth2/callback"
  ]
}

resource "kubernetes_manifest" "argo-workflows-middleware-stripprefix" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-argo-workflows-stripprefix"
      namespace = var.namespace
    }
    spec = {
      stripPrefix = {
        prefixes = [
          "/${local.argo-workflows-prefix}/"
        ]
        forceSlash = false
      }
    }
  }
}

resource "kubernetes_manifest" "argo-workflows-ingress-route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "argo-workflows"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && Path(`/${local.argo-workflows-prefix}/validate`)"
          middlewares = concat(
            [{
              name      = kubernetes_manifest.argo-workflows-middleware-stripprefix.manifest.metadata.name
              namespace = var.namespace
            }]
          )
          services = [
            {
              name      = "wf-admission-controller"
              port      = 8080
              namespace = var.namespace
            }
          ]
        },
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && Path(`/${local.argo-workflows-prefix}/mutate`)"
          middlewares = concat(
            [{
              name      = kubernetes_manifest.argo-workflows-middleware-stripprefix.manifest.metadata.name
              namespace = var.namespace
            }]
          )
          services = [
            {
              name      = "wf-admission-controller"
              port      = 8080
              namespace = var.namespace
            }
          ]
        },
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/${local.argo-workflows-prefix}`)"

          middlewares = concat(
            [{
              name      = kubernetes_manifest.argo-workflows-middleware-stripprefix.manifest.metadata.name
              namespace = var.namespace
            }]
          )

          services = [
            {
              name      = "${local.name}-server"
              port      = 2746
              namespace = var.namespace
            }
          ]
        },
      ]
    }
  }
}

resource "kubernetes_service_account_v1" "argo-admin-sa" {
  metadata {
    name      = local.admin
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'${local.admin}' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "11"
    }
  }
}

resource "kubernetes_secret_v1" "argo-admin-sa-token" {
  metadata {
    name      = "${local.admin}.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-admin-sa.metadata[0].name

    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-admin-rb" {
  metadata {
    name = local.admin
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-admin" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-admin-sa.metadata.0.name
    namespace = var.namespace
  }
}

resource "kubernetes_service_account_v1" "argo-developer-sa" {
  metadata {
    name      = local.developer
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'${local.developer}' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "10"
    }
  }
}

resource "kubernetes_secret_v1" "argo_dev_sa_token" {
  metadata {
    name      = "${local.developer}.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-developer-sa.metadata[0].name
    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-developer-rb" {
  metadata {
    name = local.developer
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-edit" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-developer-sa.metadata.0.name
    namespace = var.namespace
  }
}


resource "kubernetes_service_account_v1" "argo-view-sa" {
  metadata {
    name      = "argo-viewer"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'${local.viewer}' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "9"
    }
  }
}

resource "kubernetes_secret_v1" "argo-viewer-sa-token" {
  metadata {
    name      = "argo-viewer.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-view-sa.metadata[0].name
    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-view-rb" {
  metadata {
    name = "argo-view"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-view" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-view-sa.metadata.0.name
    namespace = var.namespace
  }
}

# Workflow Admission Controller
resource "kubernetes_role" "pod_viewer" {

  metadata {
    name      = "nebari-pod-viewer"
    namespace = var.namespace
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list"]
  }
}

resource "kubernetes_role" "workflow_viewer" {

  metadata {
    name      = "nebari-workflow-viewer"
    namespace = var.namespace
  }

  rule {
    api_groups = ["argoproj.io"]
    resources  = ["workflows", "cronworkflows"]
    verbs      = ["get", "list"]
  }
}

resource "kubernetes_service_account" "wf-admission-controller" {
  metadata {
    name      = "wf-admission-controller-sa"
    namespace = var.namespace
  }
}

resource "kubernetes_role_binding" "wf-admission-controller-pod-viewer" {
  metadata {
    name      = "wf-admission-controller-pod-viewer"
    namespace = var.namespace
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.pod_viewer.metadata.0.name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.wf-admission-controller.metadata.0.name
    namespace = var.namespace
  }
}

resource "kubernetes_role_binding" "wf-admission-controller-wf-viewer" {
  metadata {
    name      = "wf-admission-controller-wf-viewer"
    namespace = var.namespace
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.workflow_viewer.metadata.0.name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.wf-admission-controller.metadata.0.name
    namespace = var.namespace
  }
}


resource "kubernetes_secret" "keycloak-read-only-user-credentials" {
  metadata {
    name      = "keycloak-read-only-user-credentials"
    namespace = var.namespace
  }

  data = {
    username  = var.keycloak-read-only-user-credentials["username"]
    password  = var.keycloak-read-only-user-credentials["password"]
    client_id = var.keycloak-read-only-user-credentials["client_id"]
    realm     = var.keycloak-read-only-user-credentials["realm"]
  }

  type = "Opaque"
}


resource "kubernetes_manifest" "mutatingwebhookconfiguration_admission_controller" {
  count = var.nebari-workflow-controller ? 1 : 0

  manifest = {
    "apiVersion" = "admissionregistration.k8s.io/v1"
    "kind"       = "MutatingWebhookConfiguration"
    "metadata" = {
      "name" = "wf-admission-controller"
    }
    "webhooks" = [
      {
        "admissionReviewVersions" = [
          "v1",
          "v1beta1",
        ]

        "clientConfig" = {
          "url" = "https://${var.external-url}/${local.argo-workflows-prefix}/mutate"
        }

        "name" = "wf-mutating-admission-controller.${var.namespace}.svc"
        "rules" = [
          {
            "apiGroups" = [
              "argoproj.io",
            ]
            "apiVersions" = [
              "v1alpha1",
            ]
            "operations" = [
              "CREATE",
            ]
            "resources" = [
              "workflows",
              "cronworkflows",
            ]
          },
        ]
        "sideEffects" = "None"
      },
    ]
  }
}

resource "kubernetes_manifest" "validatingwebhookconfiguration_admission_controller" {
  count = var.nebari-workflow-controller ? 1 : 0
  manifest = {
    "apiVersion" = "admissionregistration.k8s.io/v1"
    "kind"       = "ValidatingWebhookConfiguration"
    "metadata" = {
      "name" = "wf-admission-controller"
    }
    "webhooks" = [
      {
        "admissionReviewVersions" = [
          "v1",
          "v1beta1",
        ]
        "clientConfig" = {
          "url" = "https://${var.external-url}/${local.argo-workflows-prefix}/validate"
        }
        "name" = "wf-validating-admission-controller.${var.namespace}.svc"
        "rules" = [
          {
            "apiGroups" = [
              "argoproj.io",
            ]
            "apiVersions" = [
              "v1alpha1",
            ]
            "operations" = [
              "CREATE",
            ]
            "resources" = [
              "workflows",
            ]
          },
        ]
        "sideEffects" = "None"
      },
    ]
  }
}

resource "kubernetes_manifest" "deployment_admission_controller" {
  count = var.nebari-workflow-controller ? 1 : 0
  manifest = {
    "apiVersion" = "apps/v1"
    "kind"       = "Deployment"
    "metadata" = {
      "name"      = "nebari-workflow-controller"
      "namespace" = var.namespace
    }
    "spec" = {
      "replicas" = 1
      "selector" = {
        "matchLabels" = {
          "app" = "nebari-workflow-controller"
        }
      }
      "template" = {
        "metadata" = {
          "labels" = {
            "app" = "nebari-workflow-controller"
          }
        }
        "spec" = {
          serviceAccountName           = kubernetes_service_account.wf-admission-controller.metadata.0.name
          automountServiceAccountToken = true
          "containers" = [
            {
              command = ["bash", "-c"]
              args    = ["python -m nebari_workflow_controller"]

              "env" = [
                {
                  "name" = "KEYCLOAK_USERNAME"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "username"
                      "name" = "keycloak-read-only-user-credentials"
                    }
                  }
                },
                {
                  "name" = "KEYCLOAK_PASSWORD"
                  "valueFrom" = {
                    "secretKeyRef" = {
                      "key"  = "password"
                      "name" = "keycloak-read-only-user-credentials"
                    }
                  }
                },
                {
                  "name"  = "KEYCLOAK_URL"
                  "value" = "https://${var.external-url}/auth/"
                },
                {
                  "name"  = "NAMESPACE"
                  "value" = var.namespace
                },
              ]
              "volumeMounts" = [
                {
                  "mountPath" = "/etc/argo"
                  "name"      = "valid-argo-roles"
                  "readOnly"  = true
                },
              ]
              "image" = "quay.io/nebari/nebari-workflow-controller:${var.workflow-controller-image-tag}"
              "name"  = "admission-controller"
            },
          ]
          "volumes" = [
            {
              "name" = "valid-argo-roles"
              "configMap" = {
                "name" = "valid-argo-roles"
              }
            },
          ]
          affinity = {
            nodeAffinity = {
              requiredDuringSchedulingIgnoredDuringExecution = {
                nodeSelectorTerms = [
                  {
                    matchExpressions = [
                      {
                        key      = var.node-group.key
                        operator = "In"
                        values   = [var.node-group.value]
                      }
                    ]
                  }
                ]
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_manifest" "service_admission_controller" {
  manifest = {
    "apiVersion" = "v1"
    "kind"       = "Service"
    "metadata" = {
      "name"      = "wf-admission-controller"
      "namespace" = var.namespace
    }
    "spec" = {
      "ports" = [
        {
          "name"       = "wf-admission-controller"
          "port"       = 8080
          "targetPort" = 8080
        },
      ]
      "selector" = {
        "app" = "nebari-workflow-controller"
      }
    }
  }
}

resource "kubernetes_config_map" "valid-argo-roles" {
  metadata {
    name      = "valid-argo-roles"
    namespace = var.namespace
  }

  data = {
    "valid-argo-roles" = jsonencode([local.admin, local.developer])
  }
}
