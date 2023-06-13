variable "name" {
  description = "Prefix name to assign to efs resource"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to resource"
  type        = map(string)
  default     = {}
}

variable "efs_throughput" {
  description = "Throughput mode for EFS filesystem (busting|provisioned)"
  type        = string
  default     = "bursting"
}

variable "efs_subnets" {
  description = "AWS VPC subnets to use for efs"
  type        = list(string)
}

variable "efs_security_groups" {
  description = "AWS security groups"
  type        = list(string)
}
