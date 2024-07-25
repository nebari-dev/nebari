resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge({ Name = var.name }, var.tags, var.vpc_tags)
}

resource "aws_subnet" "main" {
  count = length(var.aws_availability_zones)

  availability_zone       = var.aws_availability_zones[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr_block, var.vpc_cidr_newbits, count.index)
  vpc_id                  = aws_vpc.main.id
  map_public_ip_on_launch = true

  tags = merge({ Name = "${var.name}-subnet-${count.index}" }, var.tags, var.subnet_tags)

  lifecycle {
    ignore_changes = [
      availability_zone
    ]
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_route_table" "main" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_route_table_association" "main" {
  count = length(var.aws_availability_zones)

  subnet_id      = aws_subnet.main[count.index].id
  route_table_id = aws_route_table.main.id
}

resource "aws_security_group" "main" {
  name        = var.name
  description = "Main security group for infrastructure deployment"

  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ Name = var.name }, var.tags, var.security_group_tags)
}
