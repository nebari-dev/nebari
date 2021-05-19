output "credentials" {
  description = "EFS connection credentials"
  value = {
    dns_name = aws_efs_file_system.main.dns_name
  }
}
