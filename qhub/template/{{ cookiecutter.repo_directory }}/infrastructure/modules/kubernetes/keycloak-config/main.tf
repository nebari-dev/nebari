terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = "3.3.0"
    }
  }
}

resource "keycloak_realm" "realm-qhub" {
  provider = keycloak
  
  realm = "qhub"

  display_name = "QHub ${var.name}"

  smtp_server {
    host = "smtp.gmail.com"
    from = "email@test.com"

    auth {
      username = "email@test.com"
      password = "<password>"
    }
  }
}

resource "keycloak_user" "user" {
  count = length(var.users)

  realm_id = keycloak_realm.realm-qhub.id

  username = var.users[count.index].name
  enabled  = true
  email    = var.users[count.index].email

  lifecycle {
    ignore_changes = [
      first_name, last_name, email, enabled
    ]
  }

  attributes = {
    uid = var.users[count.index].uid
  }

  initial_password {
    value     = var.users[count.index].password
    temporary = false
  }
}

resource "keycloak_group" "group" {
  count = length(var.groups)

  realm_id = keycloak_realm.realm-qhub.id
  name     = var.groups[count.index].name

  attributes = {
    gid = var.groups[count.index].gid
  }
}

resource "keycloak_user_groups" "user_groups" {
  count = length(var.user_groups)

  realm_id = keycloak_realm.realm-qhub.id

  user_id = keycloak_user.user[count.index].id

  group_ids  = [
    for i in var.user_groups[count.index] : keycloak_group.group[i].id
  ]
}
