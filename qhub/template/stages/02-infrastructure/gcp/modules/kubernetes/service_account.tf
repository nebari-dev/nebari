resource "google_service_account" "main" {
  account_id   = var.name
  display_name = "${var.name} kubernetes node-group service account"
}

resource "google_project_iam_member" "main" {
  for_each = toset(local.node_group_service_account_roles)

  role   = each.value
  member = "serviceAccount:${google_service_account.main.email}"

  project = var.project_id
}
