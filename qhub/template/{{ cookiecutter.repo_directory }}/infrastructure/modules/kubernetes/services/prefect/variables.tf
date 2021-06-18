variable "jupyterhub_api_token" {
  type    = string
  default = ""
}

variable "namespace" {
  type    = string
  default = "dev"
}

variable "prefect_token" {
  type    = string
  default = ""
}

variable "image" {
  type    = string
  default = "prefecthq/prefect:0.14.22-python3.8"
}

variable "cloud_api" {
  type    = string
  default = "https://api.prefect.io"
}
