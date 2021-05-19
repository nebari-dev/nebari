# # =======================================================
# # AWS RDS + IAM Policy Setup
# # =======================================================

# resource "aws_iam_user" "psql_user" {
#   count = length(var.postgresql_additional_users)

#   name = "${var.name}-psql"
# }

# resource "aws_iam_access_key" "psql_user" {
#   user = aws_iam_user.psql_user.name
# }

# output "psql_user_secret" {
#   description = "PSQL User Access Keys"
#   value = aws_iam_access_key.psql_user.encrypted_secret
# }

# data "aws_iam_policy_document" "psql" {
#   depends_on = [
#     aws_rds_cluster.postgresql
#   ]

#   statement {
#     sid = "1"

#     effect = "Allow"

#     actions = [
#       "rds-db:connect"
#     ]

#     # should username be included with arn? var.postgresql_user?
#     resources = concat(
#       [ aws_rds_cluster.postgresql.arn ],
#       aws_rds_cluster_instance.postgresql[*].arn
#     )
#   }
# }

# resource "aws_iam_policy" "psql" {
#   name = "${var.name}-psql"
#   path = "/"
#   policy = data.aws_iam_policy_document.psql.json
# }

# resource "aws_iam_user_policy_attachment" "psql_attach" {
#   user = aws_iam_user.psql_user.name
#   policy_arn = aws_iam_policy.psql.arn
# }
