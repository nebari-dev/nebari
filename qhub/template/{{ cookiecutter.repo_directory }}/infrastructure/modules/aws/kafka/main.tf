resource "aws_kms_key" "main" {
  description = var.name

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_msk_cluster" "main" {
  cluster_name           = var.name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.kafka_instance_count

  broker_node_group_info {
    instance_type   = var.kafka_instance_type
    ebs_volume_size = var.kafka_ebs_volume_size
    client_subnets  = var.kafka_vpc_subnets
    security_groups = var.kafka_security_groups
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.main.arn

    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  tags = merge({ Name = var.name }, var.tags)
}
