variable "name" {
  description = "name prefix to assign to dask-gateway"
  type        = string
  default     = "qhub"
}

variable "namespace" {
  description = "namespace to deploy dask-gateway"
  type        = string
}

variable "jupyterhub_api_token" {
  description = "jupyterhub api token for dask-gateway"
  type        = string
}

variable "jupyterhub_api_url" {
  description = "jupyterhub api url for dask-gateway"
  type        = string
}

variable "external-url" {
  description = "External public url that dask-gateway cluster is accessible"
  type        = string
}

variable "gateway-image" {
  description = "dask gateway image to use for gateway"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "daskgateway/dask-gateway-server"
    tag  = "0.9.0"
  }
}

variable "controller-image" {
  description = "dask gateway image to use for controller"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "daskgateway/dask-gateway-server"
    tag  = "0.9.0"
  }
}

variable "cluster-image" {
  description = "default dask gateway image to use for cluster"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "daskgateway/dask-gateway"
    tag  = "0.9.0"
  }
}

variable "general-node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}

variable "worker-node-group" {
  description = "Node group key value pair for bound worker resources"
  type = object({
    key   = string
    value = string
  })
}

variable "gateway" {
  description = "gateway configuration"
  type = object({
    loglevel = string
    # Path prefix to serve dask-gateway api requests under This prefix
    # will be added to all routes the gateway manages in the traefik
    # proxy.
    prefix = string
  })
  default = {
    loglevel = "INFO"
    prefix   = "/gateway"
  }
}

variable "controller" {
  description = "controller configuration"
  type = object({
    loglevel = string
    # Max time (in seconds) to keep around records of completed clusters.
    # Default is 24 hours.
    completedClusterMaxAge = number
    # Time (in seconds) between cleanup tasks removing records of completed
    # clusters. Default is 5 minutes.
    completedClusterCleanupPeriod = number
    # Base delay (in seconds) for backoff when retrying after failures.
    backoffBaseDelay = number
    # Max delay (in seconds) for backoff when retrying after failures.
    backoffMaxDelay = number
    # Limit on the average number of k8s api calls per second.
    k8sApiRateLimit = number
    # Limit on the maximum number of k8s api calls per second.
    k8sApiRateLimitBurst = number
  })
  default = {
    loglevel                      = "INFO"
    completedClusterMaxAge        = 86400
    completedClusterCleanupPeriod = 600
    backoffBaseDelay              = 0.1
    backoffMaxDelay               = 300
    k8sApiRateLimit               = 50
    k8sApiRateLimitBurst          = 100
  }
}

variable "cluster" {
  description = "dask gateway cluster defaults"
  type = object({
    # scheduler configuration
    scheduler_cores                  = number
    scheduler_cores_limit            = number
    scheduler_memory                 = string
    scheduler_memory_limit           = string
    scheduler_extra_container_config = any
    scheduler_extra_pod_config       = any
    # worker configuration
    worker_cores                  = number
    worker_cores_limit            = number
    worker_memory                 = string
    worker_memory_limit           = string
    worker_extra_container_config = any
    worker_extra_pod_config       = any
    # additional fields
    image_pull_policy = string
    environment       = map(string)
  })
  default = {
    # scheduler configuration
    scheduler_cores                  = 1
    scheduler_cores_limit            = 1
    scheduler_memory                 = "2 G"
    scheduler_memory_limit           = "2 G"
    scheduler_extra_container_config = {}
    scheduler_extra_pod_config       = {}
    # worker configuration
    worker_cores                  = 1
    worker_cores_limit            = 1
    worker_memory                 = "2 G"
    worker_memory_limit           = "2 G"
    worker_extra_container_config = {}
    worker_extra_pod_config       = {}
    # additional fields
    image_pull_policy = "IfNotPresent"
    environment       = {}
  }
}

variable "extra_config" {
  description = "Additional dask-gateway configuration"
  default     = ""
}
