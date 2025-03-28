resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr_block

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge({ Name = var.name }, var.tags, var.vpc_tags)
}

resource "aws_subnet" "public" {
  count = length(var.aws_availability_zones)

  availability_zone = var.aws_availability_zones[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr_block, var.vpc_cidr_newbits, count.index)
  vpc_id            = aws_vpc.main.id

  tags = merge({ Name = "${var.name}-pulbic-subnet-${count.index}", "kubernetes.io/role/elb" = 1 }, var.tags, var.subnet_tags)

  lifecycle {
    ignore_changes = [
      availability_zone
    ]
  }
}

moved {
  from = aws_subnet.main
  to   = aws_subnet.public
}


resource "aws_subnet" "private" {
  count = length(var.aws_availability_zones)

  availability_zone = var.aws_availability_zones[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr_block, var.vpc_cidr_newbits, count.index + length(var.aws_availability_zones))
  vpc_id            = aws_vpc.main.id

  tags = merge({ Name = "${var.name}-private-subnet-${count.index}" }, var.tags, var.subnet_tags)

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

resource "aws_eip" "nat-gateway-eip" {
  count = length(var.aws_availability_zones)

  domain = "vpc"

  tags = merge({ Name = "${var.name}-nat-gateway-eip-${count.index}" }, var.tags)
}

resource "aws_nat_gateway" "main" {
  count = length(var.aws_availability_zones)

  allocation_id = aws_eip.nat-gateway-eip[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags       = merge({ Name = "${var.name}-nat-gateway-${count.index}" }, var.tags)
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge({ Name = var.name }, var.tags)
}

moved {
  from = aws_route_table.main
  to   = aws_route_table.public
}

resource "aws_route_table" "private" {
  count = length(var.aws_availability_zones)

  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_route_table_association" "public" {
  count = length(var.aws_availability_zones)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(var.aws_availability_zones)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
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

  egress {
    description = "Allow all ports and protocols to exit the security group"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge({ Name = var.name }, var.tags, var.security_group_tags)
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id
  tags              = merge({ Name = "${var.name}-s3-endpoint" }, var.tags)
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.main.id]
  subnet_ids          = aws_subnet.private[*].id
  tags                = merge({ Name = "${var.name}-ecr-api-endpoint" }, var.tags)
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.main.id]
  subnet_ids          = aws_subnet.private[*].id
  tags                = merge({ Name = "${var.name}-ecr-dkr-endpoint" }, var.tags)
}

resource "aws_vpc_endpoint" "elasticloadbalancing" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.elasticloadbalancing"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.main.id]
  subnet_ids          = aws_subnet.private[*].id
  tags                = merge({ Name = "${var.name}-elb-endpoint" }, var.tags)
}

resource "aws_vpc_endpoint" "sts" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.sts"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.main.id]
  subnet_ids          = aws_subnet.private[*].id
  tags                = merge({ Name = "${var.name}-sts-endpoint" }, var.tags)
}

resource "aws_vpc_endpoint" "eks" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.eks"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.main.id]
  subnet_ids          = aws_subnet.private[*].id
  tags                = merge({ Name = "${var.name}-eks-endpoint" }, var.tags)
}
