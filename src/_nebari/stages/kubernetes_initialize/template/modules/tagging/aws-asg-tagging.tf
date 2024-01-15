resource "aws_autoscaling_group_tag" "aws_eks_scaling_from_zero_labeling" {
  count                  = length(var.asg_node_group_map)
  autoscaling_group_name = element(keys(var.asg_node_group_map), count.index)

  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/dedicated"
    value               = var.asg_node_group_map[element(keys(var.asg_node_group_map), count.index)]
    propagate_at_launch = true
  }
}
