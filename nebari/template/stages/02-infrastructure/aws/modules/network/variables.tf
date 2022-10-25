variable "name" {
  description = "Prefix name to give to network resources"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to all network resource"
  type        = map(string)
  default     = {}
}

variable "vpc_tags" {
  description = "Additional tags to apply to vpc network resource"
  type        = map(string)
  default     = {}
}

variable "subnet_tags" {
  description = "Additional tags to apply to subnet network resources"
  type        = map(string)
  default     = {}
}

variable "security_group_tags" {
  description = "Additional tags to apply to security group network resource"
  type        = map(string)
  default     = {}
}

variable "aws_availability_zones" {
  description = "AWS Availability zones to operate infrastructure"
  type        = list(string)
}

variable "vpc_cidr_block" {
  description = "VPC cidr for subnets to be inside of"
  type        = string
}

variable "vpc_cidr_newbits" {
  description = "VPC cidr number of bits to support 2^N subnets"
  type        = number
  default     = 2
}
