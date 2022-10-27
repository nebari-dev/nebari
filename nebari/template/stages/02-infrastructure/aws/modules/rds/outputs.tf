output "credentials" {
  description = "connection string for master database connection"
  value = {
    arn      = aws_rds_cluster.main.arn
    username = aws_rds_cluster.main.master_username
    password = aws_rds_cluster.main.master_password
    database = aws_rds_cluster.main.database_name
    host     = aws_rds_cluster.main.endpoint
    port     = aws_rds_cluster.main.port
  }
}

# output "aws_postgresql_user_connections" {
#   description = "Database connections and iam users for each database"
# }
