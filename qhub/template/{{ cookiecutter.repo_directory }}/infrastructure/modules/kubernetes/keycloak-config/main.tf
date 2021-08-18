terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = "3.3.0"
    }
  }
}

resource "keycloak_realm" "realm-master" {
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
