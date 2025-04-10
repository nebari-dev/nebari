output "credentials" {
  description = "EFS connection credentials"
  value = {
    dns_name = aws_efs_file_system.main.dns_name
  }
}
output "efs_id" {
  description = "EFS ID"
  value       = aws_efs_file_system.main.id
}
