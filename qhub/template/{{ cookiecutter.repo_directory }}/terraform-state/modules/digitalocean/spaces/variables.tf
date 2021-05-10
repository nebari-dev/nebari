variable "name" {
  description = "Prefix name for bucket resource"
  type        = string
}

variable "region" {
  description = "Region for Digital Ocean bucket"
  type        = string
}

variable "force_destroy" {
  description = "force_destroy all bucket contents when bucket is deleted"
  type        = bool
  default     = false
}

variable "public" {
  description = "Digital Ocean s3 bucket is exposed publicly"
  type        = bool
  default     = false
}
