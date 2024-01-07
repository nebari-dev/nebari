variable "cluster_name" {
  description = "Name of the cluster."
  type        = string
}

variable "aws_region" {
  description = "AWS region is cloud provider is AWS"
  type        = string
}

variable "cloud_provider" {
  description = "Cloud provider being used in deployment"
  type        = string
}
