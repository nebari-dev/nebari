variable "namespace" {
  description = "namespace to deploy extcr"
  type        = string
}

variable "access_key_id" {
  description = "Customer's access key id for external container reg"
  type        = string
}

variable "secret_access_key" {
  description = "Customer's secret access key for external container reg"
  type        = string
}

variable "extcr_account" {
  description = "AWS Account of the external container reg"
  type        = string
}

variable "extcr_region" {
  description = "AWS Region of the external container reg"
  type        = string
}
