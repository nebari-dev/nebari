variable "name" {
  description = "Prefix name for bucket resource"
  type        = string
}

variable "tags" {
  description = "Additional tags to include with AWS S3 bucket"
  type        = map(string)
  default     = {}
}

variable "public" {
  description = "AWS s3 bucket is exposed publicly"
  type        = bool
  default     = false
}
