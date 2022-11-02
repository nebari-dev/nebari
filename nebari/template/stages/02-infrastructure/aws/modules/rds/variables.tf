variable "name" {
  description = "Prefix name to assign to AWS RDS postgresql database"
  type        = string
}

variable "tags" {
  description = "Additional tags to assign to AWS RDS postgresql database"
  type        = map(string)
  default     = {}
}

variable "rds_instance_type" {
  description = "AWS Instance type for postgresql instance"
  type        = string
  default     = "db.r4.large"
}

variable "rds_number_instances" {
  description = "AWS number of rds database instances"
  type        = number
  default     = 1
}

variable "rds_database_engine" {
  description = "aurora-postgresql"
  type        = string
  default     = "aurora-postgresql"
}

variable "database_master" {
  description = "AWS RDS master"
  type = object({
    username = string
    password = string
    database = string
  })
}
