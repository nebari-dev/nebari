# =======================================================
# Kubernetes Cluster Roles This sets up the policies that were
# previously done by using eksctl
# =======================================================

# =======================================================
# Kubernetes Cluster Policies
# =======================================================

resource "aws_iam_role" "cluster" {
  name = "${var.name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
    }]
    Version = "2012-10-17"
  })
  permissions_boundary = var.permissions_boundary
  tags                 = var.tags
}

resource "aws_iam_role_policy_attachment" "cluster-policy" {
  count = length(local.cluster_policies)

  policy_arn = local.cluster_policies[count.index]
  role       = aws_iam_role.cluster.name
}

data "aws_iam_policy_document" "cluster_encryption" {
  count = var.eks_kms_arn != null ? 1 : 0
  statement {
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ListGrants",
      "kms:DescribeKey"
    ]
    resources = [var.eks_kms_arn]
  }
}

resource "aws_iam_policy" "cluster_encryption" {
  count       = var.eks_kms_arn != null ? 1 : 0
  name        = "${var.name}-eks-encryption-policy"
  description = "IAM policy for EKS cluster encryption"
  policy      = data.aws_iam_policy_document.cluster_encryption[count.index].json
}

# Grant the EKS Cluster role KMS permissions if a key-arn is specified
resource "aws_iam_role_policy_attachment" "cluster_encryption" {
  count      = var.eks_kms_arn != null ? 1 : 0
  policy_arn = aws_iam_policy.cluster_encryption[count.index].arn
  role       = aws_iam_role.cluster.name
}

# =======================================================
# Kubernetes Node Group Policies
# =======================================================

resource "aws_iam_role" "node-group" {
  name = "${var.name}-eks-node-group-role"

  assume_role_policy = jsonencode({
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
    }]
    Version = "2012-10-17"
  })
  permissions_boundary = var.permissions_boundary
  tags                 = var.tags
}

resource "aws_iam_role_policy_attachment" "node-group-policy" {
  count = length(local.node_group_policies)

  policy_arn = local.node_group_policies[count.index]
  role       = aws_iam_role.node-group.name
}
