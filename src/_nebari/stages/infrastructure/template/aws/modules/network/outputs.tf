output "security_group_id" {
  description = "AWS security group id"
  value       = aws_security_group.main.id
}

output "public_subnet_ids" {
  description = "AWS VPC public subnet ids"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "AWS VPC private subnet ids"
  value       = aws_subnet.private[*].id
}

output "vpc_id" {
  description = "AWS VPC id"
  value       = aws_vpc.main.id
}
