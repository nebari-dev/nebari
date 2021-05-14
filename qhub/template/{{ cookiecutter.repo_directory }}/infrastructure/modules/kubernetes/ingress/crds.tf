resource "kubernetes_manifest" "ingress_route" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "ingressroutes.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "IngressRoute"
        plural   = "ingressroutes"
        singular = "ingressroute"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    routes = {
                      type = "array"
                      items = {
                        type     = "object"
                        required = ["match", "kind"]
                        properties = {
                          match = {
                            type = "string"
                          }
                          kind = {
                            type = "string"
                            enum = ["Rule"]
                          }
                          priority = {
                            type = "integer"
                          }
                          services = {
                            type = "array"
                            items = {
                              type     = "object"
                              required = ["name", "port"]
                              properties = {
                                name = {
                                  type = "string"
                                }
                                kind = {
                                  type = "string"
                                  enum = ["Service", "TraefikService"]
                                }
                                namespace = {
                                  type = "string"
                                }
                                sticky = {
                                  type = "object"
                                  properties = {
                                    cookie = {
                                      type = "object"
                                      properties = {
                                        name = {
                                          type = "string"
                                        }
                                        secure = {
                                          type = "boolean"
                                        }
                                        httpOnly = {
                                          type = "boolean"
                                        }
                                        sameSite = {
                                          type = "string"
                                          enum = ["None", "Lax", "Strict"]
                                        }
                                      }
                                    }
                                  }
                                }
                                port = {
                                  x-kubernetes-int-or-string = true
                                  pattern                    = "^[1-9]\\d*$"
                                }
                                scheme = {
                                  type = "string"
                                  enum = ["http", "https", "h2c"]
                                }
                                strategy = {
                                  type = "string"
                                  enum = ["RoundRobin"]
                                }
                                passHostHeader = {
                                  type = "boolean"
                                }
                                responseForwarding = {
                                  type = "object"
                                  properties = {
                                    flushInterval = {
                                      type = "string"
                                    }
                                  }
                                }
                                weight = {
                                  type = "integer"
                                }
                              }
                            }
                          }
                          middlewares = {
                            type = "array"
                            items = {
                              type     = "object"
                              required = ["name", "namespace"]
                              properties = {
                                name = {
                                  type = "string"
                                }
                                namespace = {
                                  type = "string"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    entryPoints = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    tls = {
                      type = "object"
                      properties = {
                        secretName = {
                          type = "string"
                        }
                        options = {
                          type     = "object"
                          required = ["name", "namespace"]
                          properties = {
                            name = {
                              type = "string"
                            }
                            namespace = {
                              type = "string"
                            }
                          }
                        }
                        store = {
                          type     = "object"
                          required = ["name", "namespace"]
                          properties = {
                            name = {
                              type = "string"
                            }
                            namespace = {
                              type = "string"
                            }
                          }
                        }
                        certResolver = {
                          type = "string"
                        }
                        domains = {
                          type = "array"
                          items = {
                            type = "object"
                            properties = {
                              main = {
                                type = "string"
                              }
                              sans = {
                                type = "array"
                                items = {
                                  type = "string"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "ingress_route_tcp" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "ingressroutetcps.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "IngressRouteTCP"
        plural   = "ingressroutetcps"
        singular = "ingressroutetcp"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    routes = {
                      type = "array"
                      items = {
                        type = "object"
                        properties = {
                          match = {
                            type = "string"
                          }
                          services = {
                            type = "array"
                            items = {
                              type     = "object"
                              required = ["name", "port"]
                              properties = {
                                name = {
                                  type = "string"
                                }
                                namespace = {
                                  type = "string"
                                }
                                port = {
                                  x-kubernetes-int-or-string = true
                                  pattern                    = "^[1-9]\\d*$"
                                }
                                weight = {
                                  type = "integer"
                                }
                                terminationDelay = {
                                  type = "integer"
                                }
                                proxyProtocol = {
                                  type     = "object"
                                  required = ["version"]
                                  properties = {
                                    version = {
                                      type    = "integer"
                                      minimum = 1
                                      maximum = 2
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    entryPoints = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    tls = {
                      type = "object"
                      properties = {
                        secretName = {
                          type = "string"
                        }
                        passthrough = {
                          type = "boolean"
                        }
                        options = {
                          type     = "object"
                          required = ["name", "namespace"]
                          properties = {
                            name = {
                              type = "string"
                            }
                            namespace = {
                              type = "string"
                            }
                          }
                        }
                        store = {
                          type     = "object"
                          required = ["name", "namespace"]
                          properties = {
                            name = {
                              type = "string"
                            }
                            namespace = {
                              type = "string"
                            }
                          }
                        }
                        certResolver = {
                          type = "string"
                        }
                        domains = {
                          type = "array"
                          items = {
                            type     = "object"
                            required = ["main"]
                            properties = {
                              main = {
                                type = "string"
                              }
                              sans = {
                                type = "array"
                                items = {
                                  type = "string"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "ingress_route_udp" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "ingressrouteudps.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "IngressRouteUDP"
        plural   = "ingressrouteudps"
        singular = "ingressrouteudp"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    routes = {
                      type = "array"
                      items = {
                        type = "object"
                        properties = {
                          services = {
                            type = "array"
                            items = {
                              type     = "object"
                              required = ["name"]
                              properties = {
                                name = {
                                  type = "string"
                                }
                                namespace = {
                                  type = "string"
                                }
                                port = {
                                  x-kubernetes-int-or-string = true
                                  pattern                    = "^[1-9]\\d*$"
                                }
                                weight = {
                                  type = "integer"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    entryPoints = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "middleware" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "middlewares.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "Middleware"
        plural   = "middlewares"
        singular = "middleware"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    addPrefix = {
                      type = "object"
                      properties = {
                        prefix = {
                          type = "string"
                        }
                      }
                    }
                    stripPrefix = {
                      type = "object"
                      properties = {
                        prefixes = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        forceSlash = {
                          type = "boolean"
                        }
                      }
                    }
                    stripPrefixRegex = {
                      type = "object"
                      properties = {
                        regex = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                      }
                    }
                    replacePath = {
                      type = "object"
                      properties = {
                        path = {
                          type = "string"
                        }
                      }
                    }
                    replacePathRegex = {
                      type = "object"
                      properties = {
                        regex = {
                          type = "string"
                        }
                        replacement = {
                          type = "string"
                        }
                      }
                    }
                    chain = {
                      type = "object"
                      properties = {
                        middlewares = {
                          type = "array"
                          items = {
                            type     = "object"
                            required = ["name", "namespace"]
                            properties = {
                              name = {
                                type = "string"
                              }
                              namespace = {
                                type = "string"
                              }
                            }
                          }
                        }
                      }
                    }
                    ipWhiteList = {
                      type = "object"
                      properties = {
                        sourceRange = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        ipStrategy = {
                          type = "object"
                          properties = {
                            depth = {
                              type = "integer"
                            }
                            excludedIPs = {
                              type = "array"
                              items = {
                                type = "string"
                              }
                            }
                          }
                        }
                      }
                    }
                    headers = {
                      type = "object"
                      properties = {
                        customRequestHeaders = {
                          type = "object"
                        }
                        customResponseHeaders = {
                          type = "object"
                        }
                        accessControlAllowCredentials = {
                          type = "boolean"
                        }
                        accessControlAllowHeaders = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        accessControlAllowMethods = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        accessControlAllowOrigin = {
                          type = "string"
                        }
                        accessControlAllowOriginList = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        accessControlExposeHeaders = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        accessControlMaxAge = {
                          type = "integer"
                        }
                        addVaryHeader = {
                          type = "boolean"
                        }
                        allowedHosts = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        hostsProxyHeaders = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        sslRedirect = {
                          type = "boolean"
                        }
                        sslTemporaryRedirect = {
                          type = "boolean"
                        }
                        sslHost = {
                          type = "string"
                        }
                        sslProxyHeaders = {
                          type = "object"
                        }
                        sslForceHost = {
                          type = "boolean"
                        }
                        stsSeconds = {
                          type = "integer"
                        }
                        stsIncludeSubdomains = {
                          type = "boolean"
                        }
                        stsPreload = {
                          type = "boolean"
                        }
                        forceSTSheader = {
                          type = "boolean"
                        }
                        frameDeny = {
                          type = "boolean"
                        }
                        customFrameOptionsValue = {
                          type = "string"
                        }
                        contentTypeNosniff = {
                          type = "boolean"
                        }
                        browserXssFilter = {
                          type = "boolean"
                        }
                        customBrowserXSSValue = {
                          type = "string"
                        }
                        contentSecurityPolicy = {
                          type = "string"
                        }
                        publicKey = {
                          type = "string"
                        }
                        referrerPolicy = {
                          type = "string"
                        }
                        featurePolicy = {
                          type = "string"
                        }
                        isDevelopment = {
                          type = "boolean"
                        }
                      }
                    }
                    errors = {
                      type = "object"
                      properties = {
                        status = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        service = {
                          type = "object"
                          properties = {
                            sticky = {
                              type = "object"
                              properties = {
                                cookie = {
                                  type = "object"
                                  properties = {
                                    name = {
                                      type = "string"
                                    }
                                    secure = {
                                      type = "boolean"
                                    }
                                    httpOnly = {
                                      type = "boolean"
                                    }
                                  }
                                }
                              }
                            }
                            namespace = {
                              type = "string"
                            }
                            kind = {
                              type = "string"
                            }
                            name = {
                              type = "string"
                            }
                            weight = {
                              type = "integer"
                            }
                            responseForwarding = {
                              type = "object"
                              properties = {
                                flushInterval = {
                                  type = "string"
                                }
                              }
                            }
                            passHostHeader = {
                              type = "boolean"
                            }
                            healthCheck = {
                              type = "object"
                              properties = {
                                path = {
                                  type = "string"
                                }
                                host = {
                                  type = "string"
                                }
                                scheme = {
                                  type = "string"
                                }
                                intervalSeconds = {
                                  type = "integer"
                                }
                                timeoutSeconds = {
                                  type = "integer"
                                }
                                headers = {
                                  type = "object"
                                }
                              }
                            }
                            strategy = {
                              type = "string"
                            }
                            scheme = {
                              type = "string"
                            }
                            port = {
                              type = "integer"
                            }
                          }
                        }
                        query = {
                          type = "string"
                        }
                      }
                    }
                    rateLimit = {
                      type = "object"
                      properties = {
                        average = {
                          type = "integer"
                        }
                        burst = {
                          type = "integer"
                        }
                        sourceCriterion = {
                          type = "object"
                          properties = {
                            ipStrategy = {
                              type = "object"
                              properties = {
                                depth = {
                                  type = "integer"
                                }
                                excludedIPs = {
                                  type = "array"
                                  items = {
                                    type = "string"
                                  }
                                }
                              }
                            }
                            requestHeaderName = {
                              type = "string"
                            }
                            requestHost = {
                              type = "boolean"
                            }
                          }
                        }
                      }
                    }
                    redirectRegex = {
                      type = "object"
                      properties = {
                        regex = {
                          type = "string"
                        }
                        replacement = {
                          type = "string"
                        }
                        permanent = {
                          type = "boolean"
                        }
                      }
                    }
                    redirectScheme = {
                      type = "object"
                      properties = {
                        scheme = {
                          type = "string"
                        }
                        port = {
                          type = "string"
                        }
                        permanent = {
                          type = "boolean"
                        }
                      }
                    }
                    basicAuth = {
                      type = "object"
                      properties = {
                        secret = {
                          type = "string"
                        }
                        realm = {
                          type = "string"
                        }
                        removeHeader = {
                          type = "boolean"
                        }
                        headerField = {
                          type = "string"
                        }
                      }
                    }
                    digestAuth = {
                      type = "object"
                      properties = {
                        secret = {
                          type = "string"
                        }
                        removeHeader = {
                          type = "boolean"
                        }
                        realm = {
                          type = "string"
                        }
                        headerField = {
                          type = "string"
                        }
                      }
                    }
                    forwardAuth = {
                      type = "object"
                      properties = {
                        address = {
                          type = "string"
                        }
                        trustForwardHeader = {
                          type = "boolean"
                        }
                        authResponseHeaders = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        tls = {
                          type = "object"
                          properties = {
                            caSecret = {
                              type = "string"
                            }
                            caOptional = {
                              type = "boolean"
                            }
                            certSecret = {
                              type = "string"
                            }
                            insecureSkipVerify = {
                              type = "boolean"
                            }
                          }
                        }
                      }
                    }
                    inFlightReq = {
                      type = "object"
                      properties = {
                        amount = {
                          type = "integer"
                        }
                        sourceCriterion = {
                          type = "object"
                          properties = {
                            ipStrategy = {
                              type = "object"
                              properties = {
                                depth = {
                                  type = "integer"
                                }
                                excludedIPs = {
                                  type = "array"
                                  items = {
                                    type = "string"
                                  }
                                }
                              }
                            }
                            requestHeaderName = {
                              type = "string"
                            }
                            requestHost = {
                              type = "boolean"
                            }
                          }
                        }
                      }
                    }
                    buffering = {
                      type = "object"
                      properties = {
                        maxRequestBodyBytes = {
                          type = "integer"
                        }
                        memRequestBodyBytes = {
                          type = "integer"
                        }
                        maxResponseBodyBytes = {
                          type = "integer"
                        }
                        memResponseBodyBytes = {
                          type = "integer"
                        }
                        retryExpression = {
                          type = "string"
                        }
                      }
                    }
                    circuitBreaker = {
                      type = "object"
                      properties = {
                        expression = {
                          type = "string"
                        }
                      }
                    }
                    compress = {
                      type = "object"
                      properties = {
                        excludedContentTypes = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                      }
                    }
                    passTLSClientCert = {
                      type = "object"
                      properties = {
                        pem = {
                          type = "boolean"
                        }
                        info = {
                          type = "object"
                          properties = {
                            notAfter = {
                              type = "boolean"
                            }
                            notBefore = {
                              type = "boolean"
                            }
                            sans = {
                              type = "boolean"
                            }
                            subject = {
                              type = "object"
                              properties = {
                                country = {
                                  type = "boolean"
                                }
                                province = {
                                  type = "boolean"
                                }
                                locality = {
                                  type = "boolean"
                                }
                                organization = {
                                  type = "boolean"
                                }
                                commonName = {
                                  type = "boolean"
                                }
                                serialNumber = {
                                  type = "boolean"
                                }
                                domainComponent = {
                                  type = "boolean"
                                }
                              }
                            }
                            issuer = {
                              type = "object"
                              properties = {
                                country = {
                                  type = "boolean"
                                }
                                province = {
                                  type = "boolean"
                                }
                                locality = {
                                  type = "boolean"
                                }
                                organization = {
                                  type = "boolean"
                                }
                                commonName = {
                                  type = "boolean"
                                }
                                serialNumber = {
                                  type = "boolean"
                                }
                                domainComponent = {
                                  type = "boolean"
                                }
                              }
                            }
                            serialNumber = {
                              type = "boolean"
                            }
                          }
                        }
                      }
                    }
                    retry = {
                      type = "object"
                      properties = {
                        attempts = {
                          type = "integer"
                        }
                      }
                    }
                    contentType = {
                      type = "object"
                      properties = {
                        autoDetect = {
                          type = "boolean"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "serverstransports" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "serverstransports.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "ServersTransport"
        plural   = "serverstransports"
        singular = "serverstransports"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    serverName = {
                      type = "string"
                    }
                    insecureSkipVerify = {
                      type = "boolean"
                    }
                    rootCAsSecrets = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    certificatesSecrets = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    maxIdleConnsPerHost = {
                      type = "integer"
                    }
                    forwardingTimeouts = {
                      type = "object"
                      properties = {
                        dialTimeout = {
                          x-kubernetes-int-or-string = true
                          pattern                    = "^[1-9](\\d+)?(ns|us|µs|μs|ms|s|m|h)?$"
                        }
                        responseHeaderTimeout = {
                          x-kubernetes-int-or-string = true
                          pattern                    = "^[1-9](\\d+)?(ns|us|µs|μs|ms|s|m|h)?$"
                        }
                        idleConnTimeout = {
                          x-kubernetes-int-or-string = true
                          pattern                    = "^[1-9](\\d+)?(ns|us|µs|μs|ms|s|m|h)?$"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "tls_option" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "tlsoptions.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "TLSOption"
        plural   = "tlsoptions"
        singular = "tlsoption"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    minVersion = {
                      type = "string"
                    }
                    maxVersion = {
                      type = "string"
                    }
                    cipherSuites = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    curvePreferences = {
                      type = "array"
                      items = {
                        type = "string"
                      }
                    }
                    clientAuth = {
                      type = "object"
                      properties = {
                        clientAuthType = {
                          type = "string"
                          enum = ["NoClientCert", "RequestClientCert", "VerifyClientCertIfGiven", "RequireAndVerifyClientCert"]
                        }
                        secretNames = {
                          type = "array"
                          items = {
                            type = "string"
                          }
                        }
                        sniStrict = {
                          type = "boolean"
                        }
                        preferServerCipherSuites = {
                          type = "boolean"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "tls_stores" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "tlsstores.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "TLSStore"
        plural   = "tlsstores"
        singular = "tlsstore"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    defaultCertificate = {
                      type = "object"
                      properties = {
                        secretName = {
                          type = "string"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}


resource "kubernetes_manifest" "traefik_service" {
  provider = kubernetes-alpha

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "traefikservices.traefik.containo.us"
    }
    spec = {
      group = "traefik.containo.us"
      names = {
        kind     = "TraefikService"
        plural   = "traefikservices"
        singular = "traefikservice"
      }
      scope = "Namespaced"
      versions = [
        {
          name    = "v1alpha1"
          served  = true
          storage = true
          schema = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                spec = {
                  type = "object"
                  properties = {
                    weighted = {
                      type = "object"
                      properties = {
                        services = {
                          type = "array"
                          items = {
                            type = "object"
                            properties = {
                              sticky = {
                                type = "object"
                                properties = {
                                  cookie = {
                                    type = "object"
                                    properties = {
                                      name = {
                                        type = "string"
                                      }
                                      secure = {
                                        type = "boolean"
                                      }
                                      httpOnly = {
                                        type = "boolean"
                                      }
                                    }
                                  }
                                }
                              }
                              namespace = {
                                type = "string"
                              }
                              kind = {
                                type = "string"
                              }
                              name = {
                                type = "string"
                              }
                              weight = {
                                type = "integer"
                              }
                              responseForwarding = {
                                type = "object"
                                properties = {
                                  flushInterval = {
                                    type = "string"
                                  }
                                }
                              }
                              passHostHeader = {
                                type = "boolean"
                              }
                              healthCheck = {
                                type = "object"
                                properties = {
                                  path = {
                                    type = "string"
                                  }
                                  host = {
                                    type = "string"
                                  }
                                  scheme = {
                                    type = "string"
                                  }
                                  intervalSeconds = {
                                    type = "integer"
                                  }
                                  timeoutSeconds = {
                                    type = "integer"
                                  }
                                  headers = {
                                    type = "object"
                                  }
                                }
                              }
                              strategy = {
                                type = "string"
                              }
                              scheme = {
                                type = "string"
                              }
                              port = {
                                type = "integer"
                              }
                            }
                          }
                        }
                        sticky = {
                          type = "object"
                          properties = {
                            cookie = {
                              type = "object"
                              properties = {
                                name = {
                                  type = "string"
                                }
                                secure = {
                                  type = "boolean"
                                }
                                httpOnly = {
                                  type = "boolean"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    mirroring = {
                      type = "object"
                      properties = {
                        weight = {
                          type = "integer"
                        }
                        responseForwarding = {
                          type = "object"
                          properties = {
                            flushInterval = {
                              type = "string"
                            }
                          }
                        }
                        passHostHeader = {
                          type = "boolean"
                        }
                        healthCheck = {
                          type = "object"
                          properties = {
                            path = {
                              type = "string"
                            }
                            host = {
                              type = "string"
                            }
                            scheme = {
                              type = "string"
                            }
                            intervalSeconds = {
                              type = "integer"
                            }
                            timeoutSeconds = {
                              type = "integer"
                            }
                            headers = {
                              type = "object"
                            }
                          }
                        }
                        strategy = {
                          type = "string"
                        }
                        scheme = {
                          type = "string"
                        }
                        port = {
                          type = "integer"
                        }
                        sticky = {
                          type = "object"
                          properties = {
                            cookie = {
                              type = "object"
                              properties = {
                                name = {
                                  type = "string"
                                }
                                secure = {
                                  type = "boolean"
                                }
                                httpOnly = {
                                  type = "boolean"
                                }
                              }
                            }
                          }
                        }
                        namespace = {
                          type = "string"
                        }
                        kind = {
                          type = "string"
                        }
                        name = {
                          type = "string"
                        }
                        mirrors = {
                          type = "array"
                          items = {
                            type = "object"
                            properties = {
                              name = {
                                type = "string"
                              }
                              kind = {
                                type = "string"
                              }
                              namespace = {
                                type = "string"
                              }
                              sticky = {
                                type = "object"
                                properties = {
                                  cookie = {
                                    type = "object"
                                    properties = {
                                      name = {
                                        type = "string"
                                      }
                                      secure = {
                                        type = "boolean"
                                      }
                                      httpOnly = {
                                        type = "boolean"
                                      }
                                    }
                                  }
                                }
                              }
                              port = {
                                type = "integer"
                              }
                              scheme = {
                                type = "string"
                              }
                              strategy = {
                                type = "string"
                              }
                              healthCheck = {
                                type = "object"
                                properties = {
                                  path = {
                                    type = "string"
                                  }
                                  host = {
                                    type = "string"
                                  }
                                  scheme = {
                                    type = "string"
                                  }
                                  intervalSeconds = {
                                    type = "integer"
                                  }
                                  timeoutSeconds = {
                                    type = "integer"
                                  }
                                  headers = {
                                    type = "object"
                                  }
                                }
                              }
                              passHostHeader = {
                                type = "boolean"
                              }
                              responseForwarding = {
                                type = "object"
                                properties = {
                                  flushInterval = {
                                    type = "string"
                                  }
                                  weight = {
                                    type = "integer"
                                  }
                                  percent = {
                                    type = "integer"
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      ]
    }
  }
}
