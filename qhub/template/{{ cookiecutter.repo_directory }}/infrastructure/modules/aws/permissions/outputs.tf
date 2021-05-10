output "credentials" {
  description = "Information about specific AWS IAM user"
  value = {
    user_arn          = aws_iam_user.main.arn,
    username          = aws_iam_user.main.name,
    access_key        = aws_iam_access_key.main.id,
    secret_key        = aws_iam_access_key.main.secret
    allowed_policies  = var.allowed_policy_actions,
    allowed_resources = var.allowed_policy_resources
  }
}
