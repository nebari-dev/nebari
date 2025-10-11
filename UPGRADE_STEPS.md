# Upgrading Keycloak from 15.0.2 (JBoss) to keycloakx 7.1.3 (Quarkus) in Nebari

## Overview

This guide covers upgrading from the `keycloak` chart (15.0.2) to the `keycloakx` chart (7.1.3) while preserving all users, realms, and configuration.

## Key Challenge

The old `keycloak` chart includes PostgreSQL as a subchart dependency, but the new `keycloakx` chart does not. To safely upgrade without losing data, we need to:
1. Extract PostgreSQL to a standalone deployment
2. Migrate the data
3. Upgrade to keycloakx pointing to the standalone database

## Prerequisites

- Existing Nebari deployment with Keycloak 15.0.2
- kubectl access to the cluster
- Terraform/OpenTofu installed

## Step 1: Deploy Standalone PostgreSQL

Add a standalone PostgreSQL Helm release in `kubernetes_keycloak/template/modules/kubernetes/keycloak-helm/main.tf`:

```terraform
# Standalone PostgreSQL database for Keycloak
# Deployed separately to allow safe upgrade from keycloak to keycloakx chart
resource "helm_release" "keycloak_postgresql" {
  name       = "keycloak-postgres-standalone"
  namespace  = var.namespace
  repository = "https://raw.githubusercontent.com/bitnami/charts/archive-full-index/bitnami"
  chart      = "postgresql"
  version    = "10.16.2"

  values = [
    jsonencode({
      image = {
        registry   = "docker.io"
        repository = "bitnamilegacy/postgresql"
        tag        = "11.14.0"
      }
      primary = {
        nodeSelector = {
          "${var.node_group.key}" = var.node_group.value
        }
      }
      auth = {
        username = "keycloak"
        password = "keycloak"
        database = "keycloak"
      }
    })
  ]
}
```

Deploy it:
```bash
cd nebari-local/stages/05-kubernetes-keycloak
tofu apply
```

Verify both PostgreSQL instances are running:
```bash
kubectl get pods -n dev | grep postgres
```

Expected output:
- `keycloak-postgresql-0` (old - from keycloak subchart)
- `keycloak-postgres-standalone-postgresql-0` (new - standalone)

## Step 2: Backup and Migrate Database

Backup from old PostgreSQL:
```bash
kubectl exec -n dev keycloak-postgresql-0 -- env PGPASSWORD=keycloak pg_dump -U keycloak -d keycloak > keycloak-backup.sql
```

Get the postgres superuser password for the new database:
```bash
kubectl get secret -n dev keycloak-postgres-standalone-postgresql -o jsonpath='{.data.postgres-password}' | base64 -d
echo
```

Create database and user in new PostgreSQL:
```bash
# Replace <POSTGRES_PASSWORD> with the actual password from above
kubectl exec -i -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -c "CREATE DATABASE keycloak;"

kubectl exec -i -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -c "CREATE USER keycloak WITH PASSWORD 'keycloak';"

kubectl exec -i -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;"
```

Restore the backup:
```bash
cat keycloak-backup.sql | kubectl exec -i -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -d keycloak
```

Verify migration:
```bash
kubectl exec -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -d keycloak -c "SELECT count(*) FROM user_entity;"
```

## Step 3: Update values.yaml for keycloakx

Update `kubernetes_keycloak/template/modules/kubernetes/keycloak-helm/values.yaml`:

```yaml
# Database configuration - connect to standalone PostgreSQL
database:
  vendor: postgres
  hostname: keycloak-postgres-standalone-postgresql
  port: 5432
  database: keycloak
  username: keycloak
  password: keycloak

# Enable database readiness check
dbchecker:
  enabled: true
```

## Step 4: Upgrade to keycloakx Chart

Update `kubernetes_keycloak/template/modules/kubernetes/keycloak-helm/main.tf`:

```terraform
resource "helm_release" "keycloak" {
  name      = "keycloak"
  namespace = var.namespace

  repository = "https://codecentric.github.io/helm-charts"
  chart      = "keycloakx"  # Changed from "keycloak"
  version    = "7.1.3"      # Changed from "15.0.2"

  # ... rest of configuration
}
```

Update the IngressRoute service name:
```terraform
resource "kubernetes_manifest" "keycloak-http" {
  manifest = {
    # ...
    spec = {
      # ...
      routes = [
        {
          # ...
          services = [
            {
              name      = "keycloak-keycloakx-http"  # Changed from "keycloak-headless"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
```

## Step 5: Fix OAuth Scopes for Keycloak 20+

Keycloak 20+ requires the `openid` scope to be explicitly requested. Update the following files:

### JupyterHub
`kubernetes_services/template/modules/kubernetes/services/jupyterhub/main.tf`:
```terraform
KeyCloakOAuthenticator = {
  # ...
  scope = ["openid", "profile", "email"]  # Add this line
  # ...
}
```

### Grafana
`kubernetes_services/template/modules/kubernetes/services/monitoring/main.tf`:
```terraform
"auth.generic_oauth" = {
  # ...
  scopes = "openid profile email"  # Changed from "profile"
  # ...
}
```

### conda-store
`kubernetes_services/template/modules/kubernetes/services/conda-store/config/conda_store_config.py`:
```python
c.GenericOAuthAuthentication.access_scope = "openid profile email"  # Changed from "profile"
```

### conda-store internal service URLs
`kubernetes_services/template/modules/kubernetes/services/conda-store/server.tf`:
```terraform
token_url_internal     = "http://keycloak-keycloakx-http.${var.namespace}.svc/auth/realms/${var.realm_id}/protocol/openid-connect/token"
realm_api_url_internal = "http://keycloak-keycloakx-http.${var.namespace}.svc/auth/admin/realms/${var.realm_id}"
```

## Step 6: Add nebari-bot User Creation

Since the keycloakx chart doesn't support startup scripts, create `nebari-bot` user via Python in the `post_deploy` hook.

Update `kubernetes_keycloak/__init__.py`:

```python
def post_deploy(
    self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
):
    """Create nebari-bot user after Keycloak is deployed."""
    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    keycloak_url = f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"
    nebari_bot_password = stage_outputs["stages/" + self.name]["keycloak_nebari_bot_password"]["value"]

    print("Creating nebari-bot user in Keycloak master realm...")

    max_attempts = 10
    retry_delay = 5  # seconds

    for attempt in range(1, max_attempts + 1):
        try:
            # Connect as root user
            admin = KeycloakAdmin(
                keycloak_url,
                username="root",
                password=self.config.security.keycloak.initial_root_password,
                realm_name="master",
                client_id="admin-cli",
                verify=False,
            )

            # Check if nebari-bot already exists
            users = admin.get_users({"username": "nebari-bot"})

            if users:
                print("nebari-bot user already exists")
                user_id = users[0]["id"]
            else:
                # Create nebari-bot user
                user_id = admin.create_user({
                    "username": "nebari-bot",
                    "enabled": True,
                    "credentials": [{
                        "type": "password",
                        "value": nebari_bot_password,
                        "temporary": False
                    }]
                })
                print("Successfully created nebari-bot user")

            # Assign admin role to nebari-bot user
            admin_role = admin.get_realm_role("admin")
            user_roles = admin.get_realm_roles_of_user(user_id)
            has_admin_role = any(role.get("name") == "admin" for role in user_roles)

            if not has_admin_role:
                admin.assign_realm_roles(user_id, [admin_role])
                print("Assigned admin role to nebari-bot user")
            else:
                print("nebari-bot user already has admin role")

            # Success - break out of retry loop
            break

        except KeycloakError as e:
            if attempt < max_attempts:
                print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to configure nebari-bot user after {max_attempts} attempts: {e}")
                sys.exit(1)
```

## Step 7: Deploy the Upgrade

```bash
# Render updated configuration
nebari render -c nebari-config.yaml -o nebari-local

# Apply Keycloak upgrade
cd nebari-local/stages/05-kubernetes-keycloak
tofu apply

# Apply Keycloak configuration
cd ../06-kubernetes-keycloak-configuration
tofu apply

# Apply services (JupyterHub, Grafana, conda-store)
cd ../07-kubernetes-services
tofu apply
```

## Step 8: Verify the Upgrade

Check Keycloak is running:
```bash
kubectl get pods -n dev | grep keycloak
```

Verify users were preserved:
```bash
kubectl exec -n dev keycloak-postgres-standalone-postgresql-0 -- env PGPASSWORD=<POSTGRES_PASSWORD> psql -U postgres -d keycloak -c "SELECT username FROM user_entity;"
```

Test authentication:
- Access JupyterHub: `https://<your-domain>/hub`
- Access Grafana: `https://<your-domain>/monitoring`
- Access conda-store: `https://<your-domain>/conda-store`

## Rollback (if needed)

If the upgrade fails, rollback using Helm:

```bash
# Check current revision
helm history keycloak -n dev

# Rollback to previous revision
helm rollback keycloak -n dev
```

## Key Differences: keycloak vs keycloakx

| Feature | keycloak 15.0.2 | keycloakx 7.1.3 |
|---------|-----------------|------------------|
| **Base** | JBoss/WildFly | Quarkus |
| **PostgreSQL** | Included as subchart | Not included (external) |
| **Database Config** | Auto-configured | Manual `database:` section |
| **Startup Scripts** | Supported | Not supported |
| **Service Name** | `keycloak-headless` | `keycloak-keycloakx-http` |
| **OAuth Scopes** | Auto-includes openid | Must explicitly request `openid` |
| **User Creation** | Startup scripts | Python `post_deploy` hook |

## Troubleshooting

### "Missing openid scope" error
- Ensure all OAuth clients request `scope = ["openid", "profile", "email"]`

### "Database not found" error
- Verify `database.hostname` points to correct service name
- Check PostgreSQL is running: `kubectl get pods -n dev | grep postgres`

### Users deleted after upgrade
- Data is in PostgreSQL persistent volume - check PVC exists
- Verify database migration completed successfully
- Check keycloakx is connecting to the correct database
