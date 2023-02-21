locals {
  name                  = "argo-workflows"
  argo-workflows-prefix = "argo"
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
      crds = {
        # crds managed manually below
        install = false
      }

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
        extraArgs = ["--auth-mode=sso", "--insecure-skip-verify"]
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
    "admin"     = ["argo_admin"]
    "developer" = ["argo_developer"]
    "analyst"   = ["argo_viewer"]
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
        }
      ]
    }
  }
}

resource "kubernetes_service_account" "argo-admin-sa" {
  metadata {
    name      = "argo-admin"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_admin' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "11"
    }
  }
}

resource "kubernetes_cluster_role_binding" "argo-admin-rb" {
  metadata {
    name = "argo-admin"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-admin" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argo-admin-sa.metadata.0.name
    namespace = var.namespace
  }
}

resource "kubernetes_service_account" "argo-dev-sa" {
  metadata {
    name      = "argo-dev"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_developer' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "10"
    }

  }
}

resource "kubernetes_cluster_role_binding" "argo-dev-rb" {
  metadata {
    name = "argo-dev"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-edit" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.argo-dev-sa.metadata.0.name
    namespace = var.namespace
  }
}


resource "kubernetes_service_account" "argo-view-sa" {
  metadata {
    name      = "argo-view"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_viewer' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "9"
    }
  }
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
    name      = kubernetes_service_account.argo-view-sa.metadata.0.name
    namespace = var.namespace
  }
}

# CRDs - These need to be updated manually when argo-workflows is upgraded - tfk8s is a useful tool for this
resource "kubernetes_manifest" "customresourcedefinition_clusterworkflowtemplates_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "clusterworkflowtemplates.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "ClusterWorkflowTemplate"
        "listKind" = "ClusterWorkflowTemplateList"
        "plural"   = "clusterworkflowtemplates"
        "shortNames" = [
          "clusterwftmpl",
          "cwft",
        ]
        "singular" = "clusterworkflowtemplate"
      }
      "scope" = "Cluster"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_cronworkflows_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "cronworkflows.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "CronWorkflow"
        "listKind" = "CronWorkflowList"
        "plural"   = "cronworkflows"
        "shortNames" = [
          "cwf",
          "cronwf",
        ]
        "singular" = "cronworkflow"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
                "status" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workflowartifactgctasks_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workflowartifactgctasks.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "WorkflowArtifactGCTask"
        "listKind" = "WorkflowArtifactGCTaskList"
        "plural"   = "workflowartifactgctasks"
        "shortNames" = [
          "wfat",
        ]
        "singular" = "workflowartifactgctask"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
                "status" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
          "subresources" = {
            "status" = {}
          }
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workfloweventbindings_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workfloweventbindings.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "WorkflowEventBinding"
        "listKind" = "WorkflowEventBindingList"
        "plural"   = "workfloweventbindings"
        "shortNames" = [
          "wfeb",
        ]
        "singular" = "workfloweventbinding"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workflows_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workflows.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "Workflow"
        "listKind" = "WorkflowList"
        "plural"   = "workflows"
        "shortNames" = [
          "wf",
        ]
        "singular" = "workflow"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "additionalPrinterColumns" = [
            {
              "description" = "Status of the workflow"
              "jsonPath"    = ".status.phase"
              "name"        = "Status"
              "type"        = "string"
            },
            {
              "description" = "When the workflow was started"
              "format"      = "date-time"
              "jsonPath"    = ".status.startedAt"
              "name"        = "Age"
              "type"        = "date"
            },
            {
              "description" = "Human readable message indicating details about why the workflow is in this condition."
              "jsonPath"    = ".status.message"
              "name"        = "Message"
              "type"        = "string"
            },
          ]
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
                "status" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"       = true
          "storage"      = true
          "subresources" = {}
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workflowtaskresults_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workflowtaskresults.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "WorkflowTaskResult"
        "listKind" = "WorkflowTaskResultList"
        "plural"   = "workflowtaskresults"
        "singular" = "workflowtaskresult"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "message" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "outputs" = {
                  "properties" = {
                    "artifacts" = {
                      "items" = {
                        "properties" = {
                          "archive" = {
                            "properties" = {
                              "none" = {
                                "type" = "object"
                              }
                              "tar" = {
                                "properties" = {
                                  "compressionLevel" = {
                                    "format" = "int32"
                                    "type"   = "integer"
                                  }
                                }
                                "type" = "object"
                              }
                              "zip" = {
                                "type" = "object"
                              }
                            }
                            "type" = "object"
                          }
                          "archiveLogs" = {
                            "type" = "boolean"
                          }
                          "artifactGC" = {
                            "properties" = {
                              "podMetadata" = {
                                "properties" = {
                                  "annotations" = {
                                    "additionalProperties" = {
                                      "type" = "string"
                                    }
                                    "type" = "object"
                                  }
                                  "labels" = {
                                    "additionalProperties" = {
                                      "type" = "string"
                                    }
                                    "type" = "object"
                                  }
                                }
                                "type" = "object"
                              }
                              "serviceAccountName" = {
                                "type" = "string"
                              }
                              "strategy" = {
                                "enum" = [
                                  "",
                                  "OnWorkflowCompletion",
                                  "OnWorkflowDeletion",
                                  "Never",
                                ]
                                "type" = "string"
                              }
                            }
                            "type" = "object"
                          }
                          "artifactory" = {
                            "properties" = {
                              "passwordSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "url" = {
                                "type" = "string"
                              }
                              "usernameSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                            }
                            "required" = [
                              "url",
                            ]
                            "type" = "object"
                          }
                          "azure" = {
                            "properties" = {
                              "accountKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "blob" = {
                                "type" = "string"
                              }
                              "container" = {
                                "type" = "string"
                              }
                              "endpoint" = {
                                "type" = "string"
                              }
                              "useSDKCreds" = {
                                "type" = "boolean"
                              }
                            }
                            "required" = [
                              "blob",
                              "container",
                              "endpoint",
                            ]
                            "type" = "object"
                          }
                          "deleted" = {
                            "type" = "boolean"
                          }
                          "from" = {
                            "type" = "string"
                          }
                          "fromExpression" = {
                            "type" = "string"
                          }
                          "gcs" = {
                            "properties" = {
                              "bucket" = {
                                "type" = "string"
                              }
                              "key" = {
                                "type" = "string"
                              }
                              "serviceAccountKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                            }
                            "required" = [
                              "key",
                            ]
                            "type" = "object"
                          }
                          "git" = {
                            "properties" = {
                              "branch" = {
                                "type" = "string"
                              }
                              "depth" = {
                                "format" = "int64"
                                "type"   = "integer"
                              }
                              "disableSubmodules" = {
                                "type" = "boolean"
                              }
                              "fetch" = {
                                "items" = {
                                  "type" = "string"
                                }
                                "type" = "array"
                              }
                              "insecureIgnoreHostKey" = {
                                "type" = "boolean"
                              }
                              "passwordSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "repo" = {
                                "type" = "string"
                              }
                              "revision" = {
                                "type" = "string"
                              }
                              "singleBranch" = {
                                "type" = "boolean"
                              }
                              "sshPrivateKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "usernameSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                            }
                            "required" = [
                              "repo",
                            ]
                            "type" = "object"
                          }
                          "globalName" = {
                            "type" = "string"
                          }
                          "hdfs" = {
                            "properties" = {
                              "addresses" = {
                                "items" = {
                                  "type" = "string"
                                }
                                "type" = "array"
                              }
                              "force" = {
                                "type" = "boolean"
                              }
                              "hdfsUser" = {
                                "type" = "string"
                              }
                              "krbCCacheSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "krbConfigConfigMap" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "krbKeytabSecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "krbRealm" = {
                                "type" = "string"
                              }
                              "krbServicePrincipalName" = {
                                "type" = "string"
                              }
                              "krbUsername" = {
                                "type" = "string"
                              }
                              "path" = {
                                "type" = "string"
                              }
                            }
                            "required" = [
                              "path",
                            ]
                            "type" = "object"
                          }
                          "http" = {
                            "properties" = {
                              "auth" = {
                                "properties" = {
                                  "basicAuth" = {
                                    "properties" = {
                                      "passwordSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                      "usernameSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                    }
                                    "type" = "object"
                                  }
                                  "clientCert" = {
                                    "properties" = {
                                      "clientCertSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                      "clientKeySecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                    }
                                    "type" = "object"
                                  }
                                  "oauth2" = {
                                    "properties" = {
                                      "clientIDSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                      "clientSecretSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                      "endpointParams" = {
                                        "items" = {
                                          "properties" = {
                                            "key" = {
                                              "type" = "string"
                                            }
                                            "value" = {
                                              "type" = "string"
                                            }
                                          }
                                          "required" = [
                                            "key",
                                          ]
                                          "type" = "object"
                                        }
                                        "type" = "array"
                                      }
                                      "scopes" = {
                                        "items" = {
                                          "type" = "string"
                                        }
                                        "type" = "array"
                                      }
                                      "tokenURLSecret" = {
                                        "properties" = {
                                          "key" = {
                                            "type" = "string"
                                          }
                                          "name" = {
                                            "type" = "string"
                                          }
                                          "optional" = {
                                            "type" = "boolean"
                                          }
                                        }
                                        "required" = [
                                          "key",
                                        ]
                                        "type" = "object"
                                      }
                                    }
                                    "type" = "object"
                                  }
                                }
                                "type" = "object"
                              }
                              "headers" = {
                                "items" = {
                                  "properties" = {
                                    "name" = {
                                      "type" = "string"
                                    }
                                    "value" = {
                                      "type" = "string"
                                    }
                                  }
                                  "required" = [
                                    "name",
                                    "value",
                                  ]
                                  "type" = "object"
                                }
                                "type" = "array"
                              }
                              "url" = {
                                "type" = "string"
                              }
                            }
                            "required" = [
                              "url",
                            ]
                            "type" = "object"
                          }
                          "mode" = {
                            "format" = "int32"
                            "type"   = "integer"
                          }
                          "name" = {
                            "type" = "string"
                          }
                          "optional" = {
                            "type" = "boolean"
                          }
                          "oss" = {
                            "properties" = {
                              "accessKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "bucket" = {
                                "type" = "string"
                              }
                              "createBucketIfNotPresent" = {
                                "type" = "boolean"
                              }
                              "endpoint" = {
                                "type" = "string"
                              }
                              "key" = {
                                "type" = "string"
                              }
                              "lifecycleRule" = {
                                "properties" = {
                                  "markDeletionAfterDays" = {
                                    "format" = "int32"
                                    "type"   = "integer"
                                  }
                                  "markInfrequentAccessAfterDays" = {
                                    "format" = "int32"
                                    "type"   = "integer"
                                  }
                                }
                                "type" = "object"
                              }
                              "secretKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "securityToken" = {
                                "type" = "string"
                              }
                            }
                            "required" = [
                              "key",
                            ]
                            "type" = "object"
                          }
                          "path" = {
                            "type" = "string"
                          }
                          "raw" = {
                            "properties" = {
                              "data" = {
                                "type" = "string"
                              }
                            }
                            "required" = [
                              "data",
                            ]
                            "type" = "object"
                          }
                          "recurseMode" = {
                            "type" = "boolean"
                          }
                          "s3" = {
                            "properties" = {
                              "accessKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "bucket" = {
                                "type" = "string"
                              }
                              "createBucketIfNotPresent" = {
                                "properties" = {
                                  "objectLocking" = {
                                    "type" = "boolean"
                                  }
                                }
                                "type" = "object"
                              }
                              "encryptionOptions" = {
                                "properties" = {
                                  "enableEncryption" = {
                                    "type" = "boolean"
                                  }
                                  "kmsEncryptionContext" = {
                                    "type" = "string"
                                  }
                                  "kmsKeyId" = {
                                    "type" = "string"
                                  }
                                  "serverSideCustomerKeySecret" = {
                                    "properties" = {
                                      "key" = {
                                        "type" = "string"
                                      }
                                      "name" = {
                                        "type" = "string"
                                      }
                                      "optional" = {
                                        "type" = "boolean"
                                      }
                                    }
                                    "required" = [
                                      "key",
                                    ]
                                    "type" = "object"
                                  }
                                }
                                "type" = "object"
                              }
                              "endpoint" = {
                                "type" = "string"
                              }
                              "insecure" = {
                                "type" = "boolean"
                              }
                              "key" = {
                                "type" = "string"
                              }
                              "region" = {
                                "type" = "string"
                              }
                              "roleARN" = {
                                "type" = "string"
                              }
                              "secretKeySecret" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "useSDKCreds" = {
                                "type" = "boolean"
                              }
                            }
                            "type" = "object"
                          }
                          "subPath" = {
                            "type" = "string"
                          }
                        }
                        "required" = [
                          "name",
                        ]
                        "type" = "object"
                      }
                      "type" = "array"
                    }
                    "exitCode" = {
                      "type" = "string"
                    }
                    "parameters" = {
                      "items" = {
                        "properties" = {
                          "default" = {
                            "type" = "string"
                          }
                          "description" = {
                            "type" = "string"
                          }
                          "enum" = {
                            "items" = {
                              "type" = "string"
                            }
                            "type" = "array"
                          }
                          "globalName" = {
                            "type" = "string"
                          }
                          "name" = {
                            "type" = "string"
                          }
                          "value" = {
                            "type" = "string"
                          }
                          "valueFrom" = {
                            "properties" = {
                              "configMapKeyRef" = {
                                "properties" = {
                                  "key" = {
                                    "type" = "string"
                                  }
                                  "name" = {
                                    "type" = "string"
                                  }
                                  "optional" = {
                                    "type" = "boolean"
                                  }
                                }
                                "required" = [
                                  "key",
                                ]
                                "type" = "object"
                              }
                              "default" = {
                                "type" = "string"
                              }
                              "event" = {
                                "type" = "string"
                              }
                              "expression" = {
                                "type" = "string"
                              }
                              "jqFilter" = {
                                "type" = "string"
                              }
                              "jsonPath" = {
                                "type" = "string"
                              }
                              "parameter" = {
                                "type" = "string"
                              }
                              "path" = {
                                "type" = "string"
                              }
                              "supplied" = {
                                "type" = "object"
                              }
                            }
                            "type" = "object"
                          }
                        }
                        "required" = [
                          "name",
                        ]
                        "type" = "object"
                      }
                      "type" = "array"
                    }
                    "result" = {
                      "type" = "string"
                    }
                  }
                  "type" = "object"
                }
                "phase" = {
                  "type" = "string"
                }
                "progress" = {
                  "type" = "string"
                }
              }
              "required" = [
                "metadata",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workflowtasksets_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workflowtasksets.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "WorkflowTaskSet"
        "listKind" = "WorkflowTaskSetList"
        "plural"   = "workflowtasksets"
        "shortNames" = [
          "wfts",
        ]
        "singular" = "workflowtaskset"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
                "status" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
          "subresources" = {
            "status" = {}
          }
        },
      ]
    }
  }
}

resource "kubernetes_manifest" "customresourcedefinition_workflowtemplates_argoproj_io" {
  manifest = {
    "apiVersion" = "apiextensions.k8s.io/v1"
    "kind"       = "CustomResourceDefinition"
    "metadata" = {
      "annotations" = {
      }
      "name" = "workflowtemplates.argoproj.io"
    }
    "spec" = {
      "group" = "argoproj.io"
      "names" = {
        "kind"     = "WorkflowTemplate"
        "listKind" = "WorkflowTemplateList"
        "plural"   = "workflowtemplates"
        "shortNames" = [
          "wftmpl",
        ]
        "singular" = "workflowtemplate"
      }
      "scope" = "Namespaced"
      "versions" = [
        {
          "name" = "v1alpha1"
          "schema" = {
            "openAPIV3Schema" = {
              "properties" = {
                "apiVersion" = {
                  "type" = "string"
                }
                "kind" = {
                  "type" = "string"
                }
                "metadata" = {
                  "type" = "object"
                }
                "spec" = {
                  "type"                                 = "object"
                  "x-kubernetes-map-type"                = "atomic"
                  "x-kubernetes-preserve-unknown-fields" = true
                }
              }
              "required" = [
                "metadata",
                "spec",
              ]
              "type" = "object"
            }
          }
          "served"  = true
          "storage" = true
        },
      ]
    }
  }
}
