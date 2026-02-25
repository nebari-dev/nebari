variable "namespace" {
  description = "Namespace for helm chart resource"
  type        = string
}

variable "cluster-name" {
  description = "Cluster name for kubernetes cluster"
  type        = string
}

variable "aws_region" {
  description = "AWS Region that cluster autoscaler is running"
  type        = string
}

variable "overrides" {
  description = "Helm overrides to apply"
  type        = list(string)
  default     = []
}

variable "iam_role_arn" {
  description = "IAM role ARN for Cluster Autoscaler (IRSA)"
  type        = string
}
