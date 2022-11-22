resource "aws_resourcegroups_group" "main" {
  name        = var.project
  description = "project ${var.project} - environment ${var.environment}"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.project]
        },
        {
          Key    = "Environment"
          Values = [var.environment]
        },
        {
          Key    = "Owner"
          Values = ["terraform", "terraform-state"]
        }
      ]
    })
  }

  tags = merge({
    Description = "AWS resources project=${var.project} and environment=${var.environment}"
  }, var.tags)

}
