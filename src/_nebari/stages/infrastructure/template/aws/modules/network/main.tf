resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge({ Name = var.name }, var.tags, var.vpc_tags)
}

resource "aws_subnet" "main" {
  count = length(var.aws_availability_zones)

  availability_zone = var.aws_availability_zones[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr_block, var.vpc_cidr_newbits, count.index)
  vpc_id            = aws_vpc.main.id

  tags = merge({ Name = "${var.name}-subnet-${count.index}" }, var.tags, var.subnet_tags)

  lifecycle {
    ignore_changes = [
      availability_zone
    ]
  }
}

resource "aws_security_group" "main" {
  name        = var.name
  description = "Main security group for infrastructure deployment"

  vpc_id = aws_vpc.main.id

  ingress {
    description = "Allow all ports and protocols to enter the security group"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr_block]
  }

  #trivy:ignore:AVD-AWS-0104
  egress {
    description = "Allow all ports and protocols to exit the security group"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ Name = var.name }, var.tags, var.security_group_tags)
}
