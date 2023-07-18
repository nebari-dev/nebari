resource "aws_rds_cluster" "main" {
  cluster_identifier = var.name

  engine = var.rds_database_engine

  database_name   = var.database_master.database
  master_username = var.database_master.username
  master_password = var.database_master.password

  backup_retention_period             = 5
  preferred_backup_window             = "07:00-09:00"
  skip_final_snapshot                 = true
  iam_database_authentication_enabled = true

  # NOTE - this should be removed when not in dev mode to reduce risk
  # of downtime
  apply_immediately = true

  tags = merge({
    Name        = var.name
    Description = "RDS database for ${var.name}-rds-cluster"
  }, var.tags)
}

resource "aws_rds_cluster_instance" "main" {
  count      = 1
  identifier = "${var.name}-cluster-instance-${count.index}"

  cluster_identifier  = aws_rds_cluster.main.id
  instance_class      = var.rds_instance_type
  publicly_accessible = true

  engine = var.rds_database_engine

  tags = merge({
    Name        = "${var.name}-cluster-instance-${count.index}"
    Description = "RDS database for ${var.name}-rds-cluster instances"
  }, var.tags)
}
