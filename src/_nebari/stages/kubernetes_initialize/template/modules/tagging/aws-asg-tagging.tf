data "aws_eks_node_group" "user" {
  count           = var.cloud_provider == "aws" ? 1 : 0
  cluster_name    = var.cluster_name
  node_group_name = "user"
}

resource "aws_autoscaling_group_tag" "dedicated_user" {
  for_each = toset(
    [for asg in flatten(
      [for resources in data.aws_eks_node_group[0].user.resources : resources.autoscaling_groups]
      ) : asg.name
    ]
  )
  autoscaling_group_name = each.value
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/dedicated"
    value               = "user"
    propagate_at_launch = true
  }
  depends_on = [
    data.aws_eks_node_group[0].user
  ]
}

data "aws_eks_node_group" "worker" {
  count           = var.cloud_provider == "aws" ? 1 : 0
  cluster_name    = var.cluster_name
  node_group_name = "worker"
}

resource "aws_autoscaling_group_tag" "dedicated_worker" {
  for_each = toset(
    [for asg in flatten(
      [for resources in data.aws_eks_node_group[0].worker.resources : resources.autoscaling_groups]
      ) : asg.name
    ]
  )
  autoscaling_group_name = each.value
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/dedicated"
    value               = "worker"
    propagate_at_launch = true
  }
  depends_on = [
    data.aws_eks_node_group[0].worker,
  ]
}
