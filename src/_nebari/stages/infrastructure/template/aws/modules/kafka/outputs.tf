output "credentials" {
  description = "Important credentials for connecting to MSK cluster"
  value = {
    zookeeper_host        = aws_msk_cluster.main.zookeeper_connect_string
    bootstrap_brokers     = aws_msk_cluster.main.bootstrap_brokers
    bootstrap_brokers_tls = aws_msk_cluster.main.bootstrap_brokers_tls
  }
}
