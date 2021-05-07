resource "aws_efs_file_system" "main" {
  creation_token = var.name

  encrypted = true

  throughput_mode = var.efs_throughput

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_efs_mount_target" "main" {
  count = length(var.efs_subnets)

  file_system_id = aws_efs_file_system.main.id

  subnet_id = var.efs_subnets[count.index]

  security_groups = var.efs_security_groups
}
