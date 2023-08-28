resource "aws_iam_user" "main" {
  name = var.name

  tags = merge({ Name = var.name }, var.tags)
}

resource "aws_iam_access_key" "main" {
  user = aws_iam_user.main.name
}

data "aws_iam_policy_document" "main" {
  depends_on = [
    aws_iam_user.main,
    aws_iam_access_key.main
  ]

  statement {
    sid = "1"

    effect = "Allow"

    actions   = var.allowed_policy_actions
    resources = var.allowed_policy_resources
  }
}

resource "aws_iam_policy" "main" {
  name   = var.name
  path   = "/"
  policy = data.aws_iam_policy_document.main.json
}

resource "aws_iam_user_policy_attachment" "main" {
  user       = aws_iam_user.main.name
  policy_arn = aws_iam_policy.main.arn
}
