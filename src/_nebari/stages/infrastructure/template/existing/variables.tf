variable "kube_context" {
  description = "Optional kubernetes context to use to connect to kubernetes cluster"
  type        = string
}

variable "metallb_ip_max" {
  description = "Maximum IP address for MetalLB"
  type        = string
  default     = "192.168.3.92"
}
variable "metallb_ip_min" {
  description = "Minimum IP address for MetalLB"
  type        = string
  default     = "192.168.3.90"
}
