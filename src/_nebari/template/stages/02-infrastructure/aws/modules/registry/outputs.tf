output "credentials" {
  description = "ECR credentials"
  value = {
    arn            = aws_ecr_repository.main.arn
    repository_url = aws_ecr_repository.main.repository_url
  }
}
