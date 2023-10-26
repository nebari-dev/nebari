output "security_group_id" {
  description = "AWS security group id"
  value       = aws_security_group.main.id
}

output "subnet_ids" {
  description = "AWS VPC subnet ids"
  value       = aws_subnet.main[*].id
}

output "vpc_id" {
  description = "AWS VPC id"
  value       = aws_vpc.main.id
}
