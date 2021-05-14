resource "postgresql_extension" "main" {
  count = length(var.postgresql_extensions)

  name = var.postgresql_extensions[count.index]
}

resource "postgresql_role" "main" {
  count = length(var.postgresql_additional_users)

  name     = var.postgresql_additional_users[count.index].username
  login    = true
  password = var.postgresql_additional_users[count.index].password

  create_database = false
  create_role     = false
}

resource "postgresql_database" "main" {
  depends_on = [
    postgresql_role.main
  ]

  count = length(var.postgresql_additional_users)

  name  = var.postgresql_additional_users[count.index].database
  owner = var.postgresql_additional_users[count.index].username
}
