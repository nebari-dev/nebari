variable "cluster_name" {
  description = "Name of the cluster."
  type        = string
}
variable "aws_region" {
  description = "AWS Region that cluster autoscaler is running"
  type        = string
}
