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
}

variable "existing_security_group_id" {
  description = "Existing security group ID to use for Kubernetes resources"
  type        = string
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
}

variable "vpc_cidr_block" {
  description = "VPC cidr block for infastructure"
  type        = string
}

variable "kubeconfig_filename" {
  description = "Kubernetes kubeconfig written to filesystem"
  type        = string
}
