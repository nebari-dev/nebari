variable "name" {
  description = "Prefix name to assign to Nebari resources"
  type        = string
}

variable "environment" {
  description = "Environment to create Kubernetes resources"
  type        = string
}

variable "existing_subnet_ids" {
  description = "Existing VPC ID to use for Kubernetes resources"
  type        = list(string)
  default     = ["subnet-05b2b1f41f0b1d8a6", "subnet-017efc3309fbca2da"] # null
}

variable "existing_security_group_id" {
  description = "Existing security group ID to use for Kubernetes resources"
  type        = string
  default     = "sg-0e2c865bdd8824b1a" # null
}

variable "region" {
  description = "AWS region for EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "AWS kubernetes version for EKS cluster"
  type        = string
}

variable "node_groups" {
  description = "AWS node groups"
  type = list(object({
    name          = string
    instance_type = string
    gpu           = bool
    min_size      = number
    desired_size  = number
    max_size      = number
    single_subnet = bool
  }))
}

variable "availability_zones" {
  description = "AWS availability zones within AWS region"
  type        = list(string)
  default     = []
}

variable "vpc_cidr_block" {
  description = "VPC cidr block for infastructure"
  type        = string
  default     = "10.10.0.0/16"
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
  default     = null
}
