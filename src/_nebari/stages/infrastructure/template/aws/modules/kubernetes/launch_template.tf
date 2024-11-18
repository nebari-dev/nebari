# https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html#launch-template-basics
data "cloudinit_config" "user_data" {
  for_each      = { for k, v in var.node_groups : k => v if lookup(v, "launch_template", null) != null }
  gzip          = false
  base64_encode = true
  boundary      = "//"

  # Optional Pre-Bootstrap Script
  dynamic "part" {
    for_each = lookup(each.value.launch_template, "pre_bootstrap_script", null) != null ? [1] : []
    content {
      content_type = "text/x-shellscript; charset=us-ascii"
      content = templatefile("${path.module}/files/pre_bootstrap.sh.tpl", {
        bootstrap_env       = jsonencode(lookup(each.value.launch_template, "bootstrap_env_vars", {}))
        kubelet_extra_args  = lookup(each.value.launch_template, "kubelet_extra_args", "")
        pre_bootstra_script = each.value.launch_template.pre_bootstrap_script
      })
    }
  }

  # Main Bootstrap Command
  part {
    content_type = "text/x-shellscript; charset=us-ascii"
    content = templatefile("${path.module}/files/bootstrap.sh.tpl", {
      ami_id                 = lookup(each.value.launch_template, "ami_id", "")
      cluster_endpoint       = aws_eks_cluster.main.endpoint
      cluster_cert_authority = aws_eks_cluster.main.certificate_authority[0].data
      bootstrap_env          = jsonencode(lookup(each.value.launch_template, "bootstrap_env_vars", {}))
      node_group_name        = each.value.name
      kubelet_extra_args     = lookup(each.value.launch_template, "kubelet_extra_args", "")
      cluster_name           = aws_eks_cluster.main.name
    })
  }
}

## aws_launch_template user_data invocation
## If using a Custom AMI, then the /etc/eks/bootstrap cmds and args must be included/modified,
## otherwise, on default AWS EKS Node AMI, the bootstrap cmd is appended automatically
## AWS transparently creates a copy of your LaunchTemplate and actually uses that copy then for the node group. If you DONT use a custom AMI,
## then the default user-data for bootstrapping a cluster is merged in the copy.
resource "aws_launch_template" "main" {
  for_each = {
    for node_group in var.node_groups :
    node_group.name => node_group
    if node_group.launch_template != null
  }

  name_prefix            = "eks-${var.name}-${each.value.name}-"
  description            = format("Nebari Managed Launch Template for %s", each.value.name)
  update_default_version = true

  # If using a custom AMI, then the AMI ID must be specified else the default EKS AMI is used
  image_id = lookup(each.value.launch_template, "ami_id", null)

  network_interfaces {
    associate_public_ip_address = false
    delete_on_termination       = true
    security_groups             = var.cluster_security_groups
  }

  metadata_options {
    http_tokens            = "required"
    http_endpoint          = "enabled"
    instance_metadata_tags = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 50
      volume_type = "gp2"
    }
  }

  user_data = data.cloudinit_config.user_data[each.key].rendered
}
