locals {
  cluster_policies = concat([
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    "arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy",
  ], var.cluster_additional_policies)

  node_group_policies = concat([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy",
    aws_iam_policy.worker_autoscaling.arn
  ], var.node_group_additional_policies)

  gpu_node_group_names = [for node_group in var.node_groups : node_group.name if node_group.gpu == true]
}
