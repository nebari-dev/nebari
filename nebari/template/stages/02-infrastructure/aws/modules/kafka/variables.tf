variable "name" {
  description = "Name to give kafka cluster"
  type        = string
}

variable "tags" {
  description = "Tags for kafka cluster"
  type        = map(string)
  default     = {}
}

variable "kafka_version" {
  description = "Kafka server version"
  type        = string
  default     = "2.3.1"
}

variable "kafka_instance_count" {
  description = "Number of nodes to run Kafka cluster on"
  type        = number
  default     = 2
}

variable "kafka_instance_type" {
  description = "AWS Instance type to run Kafka cluster on"
  type        = string
  default     = "kafka.m5.large"
}

variable "kafka_ebs_volume_size" {
  description = "AWS EBS volume size (GB) to use for Kafka broker storage"
  type        = number
  default     = 100
}

variable "kafka_vpc_subnets" {
  description = "Kafka VPC subnets to run cluster on"
  type        = list(string)
}

variable "kafka_security_groups" {
  description = "Kafka security groups to run cluster on"
  type        = list(string)
}
