variable "kube_context" {
  description = "Optional kubernetes context to use to connect to kubernetes cluster"
  type        = string
  default     = "default"
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file to use to connect to kubernetes cluster"
  type        = string
}

variable "metallb_ip_max" {
  description = "Maximum IP address for MetalLB"
  type        = string
  default     = ""
}

variable "metallb_ip_min" {
  description = "Minimum IP address for MetalLB"
  type        = string
  default     = ""
}

variable "metallb_enabled" {
  description = "Enable MetalLB"
  type        = bool
  default     = false
}
