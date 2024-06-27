data "aws_partition" "current" {}

resource "aws_eks_cluster" "main" {
  name     = var.name
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    security_group_ids = var.cluster_security_groups
    subnet_ids         = var.cluster_subnets

    endpoint_public_access  = var.endpoint_public_access
    endpoint_private_access = var.endpoint_private_access
    public_access_cidrs     = var.public_access_cidrs
  }

  depends_on = [
    aws_iam_role_policy_attachment.cluster-policy,
  ]

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_launch_template" "main" {
  # Invoke launch_template only if var.extra_ssl_certificates is not null
  count = var.extra_ssl_certificates == null ? 0 : length(var.node_groups)

  #key_name                      = var.key_name
  name                          = var.node_groups[count.index].name

  vpc_security_group_ids = var.cluster_security_groups

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = 50
      volume_type = "gp2"
    }
  }
  ## https://docs.aws.amazon.com/eks/latest/userguide/launch-templates.html#launch-template-basics ##
  ## https://stackoverflow.com/questions/68894525/how-to-pass-kubelet-extra-args-to-aws-eks-node-group-created-by-terraform-aws ##
  user_data                     = base64encode(<<-EOF
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="//"

--//
Content-Type: text/x-shellscript; charset="us-ascii"
#!/bin/bash
cat <<-EOT >> /etc/pki/ca-trust/source/anchors/client.pem
${var.extra_ssl_certificates}
EOT
sudo update-ca-trust extract
## If using a Custom AMI, then the following bootstrap cmds and args must be included/modified,
## otherwise, on AWS EKS Node AMI, the /etc/eks/bootstrap.sh cmd is appended automatically
#set -ex
#B64_CLUSTER_CA=${aws_eks_cluster.main.certificate_authority[0].data}
#API_SERVER_URL=${aws_eks_cluster.main.endpoint}
#K8S_CLUSTER_DNS_IP=172.20.0.10
#/etc/eks/bootstrap.sh ${aws_eks_cluster.main.name} --kubelet-extra-args '--node-labels=eks.amazonaws.com/nodegroup-image=ami-0c7e1dd70292cb6c6,dedicated=${var.node_groups[count.index].name},eks.amazonaws.com/capacityType=ON_DEMAND,eks.amazonaws.com/nodegroup=${var.node_groups[count.index].name} --max-pods=58' --b64-cluster-ca $B64_CLUSTER_CA --apiserver-endpoint $API_SERVER_URL --dns-cluster-ip $K8S_CLUSTER_DNS_IP --use-max-pods false

--//--\
  EOF
  )
}

resource "aws_eks_node_group" "main" {
  count = length(var.node_groups)

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = var.node_groups[count.index].name
  node_role_arn   = aws_iam_role.node-group.arn
  subnet_ids      = var.node_groups[count.index].single_subnet ? [element(var.cluster_subnets, 0)] : var.cluster_subnets

  instance_types = [var.node_groups[count.index].instance_type]
  ami_type       = var.node_groups[count.index].gpu == true ? "AL2_x86_64_GPU" : "AL2_x86_64"
  disk_size      = var.extra_ssl_certificates == null ? 50 : null

  scaling_config {
    min_size     = var.node_groups[count.index].min_size
    desired_size = var.node_groups[count.index].desired_size
    max_size     = var.node_groups[count.index].max_size
  }

  labels = {
    "dedicated" = var.node_groups[count.index].name
  }

  lifecycle {
    ignore_changes = [
      scaling_config[0].desired_size,
    ]
  }
  # Invoke launch_template only if var.extra_ssl_certificates is not null
  dynamic "launch_template" {
    for_each = var.extra_ssl_certificates == null ? [] : [1]
    content {
      id = aws_launch_template.main[count.index].id
      #version = aws_launch_template.main[count.index].default_version
      version = aws_launch_template.main[count.index].latest_version
    }
  }

  # Ensure that IAM Role permissions are created before and deleted
  # after EKS Node Group handling.  Otherwise, EKS will not be able to
  # properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node-group-policy,
  ]

  tags = merge({
    "k8s.io/cluster-autoscaler/node-template/label/dedicated" = var.node_groups[count.index].name
    propagate_at_launch                                       = true
  }, var.tags)
}

data "aws_eks_cluster_auth" "main" {
  name = aws_eks_cluster.main.name
}

resource "aws_eks_addon" "aws-ebs-csi-driver" {
  # required for Kubernetes v1.23+ on AWS
  addon_name                  = "aws-ebs-csi-driver"
  cluster_name                = aws_eks_cluster.main.name
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  configuration_values = jsonencode({
    controller = {
      nodeSelector = {
        "eks.amazonaws.com/nodegroup" = "general"
      }
    }
  })

  # Ensure cluster and node groups are created
  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main,
  ]
}

resource "aws_eks_addon" "coredns" {
  addon_name   = "coredns"
  cluster_name = aws_eks_cluster.main.name

  configuration_values = jsonencode({
    nodeSelector = {
      "eks.amazonaws.com/nodegroup" = "general"
    }
  })

  # Ensure cluster and node groups are created
  depends_on = [
    aws_eks_cluster.main,
    aws_eks_node_group.main,
  ]
}

data "tls_certificate" "this" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "oidc_provider" {
  client_id_list  = ["sts.${data.aws_partition.current.dns_suffix}"]
  thumbprint_list = data.tls_certificate.this.certificates[*].sha1_fingerprint
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = merge(
    { Name = "${var.name}-eks-irsa" },
    var.tags
  )
}
