variable "name" {
  description = "Prefix name to use to annotate permission resources"
  type        = string
}

variable "tags" {
  description = "AWS iam additional tags"
  type        = map(string)
  default     = {}
}

variable "allowed_policy_actions" {
  description = "Actions to allow IAM user to perform"
  type        = list(string)
  default     = []
}

variable "allowed_policy_resources" {
  description = "Allowed AWS arns for user to have access to"
  type        = list(string)
  default     = []
}
