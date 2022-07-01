import logging
import os

import requests
from conda_store_server import api, orm, schema
from conda_store_server.server.auth import GenericOAuthAuthentication
from conda_store_server.server.utils import get_conda_store
from conda_store_server.storage import S3Storage

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/home/conda/"
c.CondaStore.database_url = "postgresql+psycopg2://${postgres-username}:${postgres-password}@${postgres-service}/conda-store"
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "775"
c.CondaStore.conda_included_packages = ["ipykernel"]

c.S3Storage.internal_endpoint = "${minio-service}:9000"
c.S3Storage.internal_secure = False
c.S3Storage.external_endpoint = "${external-url}:9080"
c.S3Storage.external_secure = True
c.S3Storage.access_key = "${minio-username}"
c.S3Storage.secret_key = "${minio-password}"
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"


# ==================================
#        server settings
# ==================================
c.CondaStoreServer.log_level = logging.INFO
c.CondaStoreServer.enable_ui = True
c.CondaStoreServer.enable_api = True
c.CondaStoreServer.enable_registry = True
c.CondaStoreServer.enable_metrics = True
c.CondaStoreServer.address = "0.0.0.0"
c.CondaStoreServer.port = 5000
# This MUST start with `/`
c.CondaStoreServer.url_prefix = "/conda-store"


# ==================================
#         auth settings
# ==================================

c.GenericOAuthAuthentication.access_token_url = "${openid-config.token_url}"
c.GenericOAuthAuthentication.authorize_url = "${openid-config.authentication_url}"
c.GenericOAuthAuthentication.user_data_url = "${openid-config.userinfo_url}"
c.GenericOAuthAuthentication.oauth_callback_url = (
    "https://${external-url}/conda-store/oauth_callback"
)
c.GenericOAuthAuthentication.client_id = "${openid-config.client_id}"
c.GenericOAuthAuthentication.client_secret = "${openid-config.client_secret}"
c.GenericOAuthAuthentication.access_scope = "profile"
c.GenericOAuthAuthentication.user_data_key = "preferred_username"
c.GenericOAuthAuthentication.tls_verify = False


class KeyCloakAuthentication(GenericOAuthAuthentication):
    def authenticate(self, request):
        # 1. using the callback_url code and state in request
        oauth_access_token = self._get_oauth_token(request)
        if oauth_access_token is None:
            return None  # authentication failed

        response = requests.get(
            self.user_data_url,
            headers={"Authorization": f"Bearer {oauth_access_token}"},
            verify=self.tls_verify,
        )
        response.raise_for_status()
        user_data = response.json()

        role_mappings = {
            "conda_store_admin": "admin",
            "conda_store_developer": "developer",
            "conda_store_viewer": "viewer",
        }
        roles = {
            role_mappings[role]
            for role in user_data.get("roles", [])
            if role in role_mappings
        }
        username = user_data["preferred_username"]
        namespaces = {username, "global", "nebari-git"}
        role_bindings = {
            f"{username}/*": {"admin"},
            "nebari-git/*": {"viewer"},
            "global/*": roles,
        }

        for group in user_data.get("groups", []):
            # Use only the base name of Keycloak groups
            group_name = os.path.basename(group)
            namespaces.add(group_name)
            role_bindings[f"{group_name}/*"] = roles

        conda_store = get_conda_store()
        for namespace in namespaces:
            _namespace = api.get_namespace(conda_store.db, name=namespace)
            if _namespace is None:
                conda_store.db.add(orm.Namespace(name=namespace))
                conda_store.db.commit()

        return schema.AuthenticationToken(
            primary_namespace=username,
            role_bindings=role_bindings,
        )


c.CondaStoreServer.authentication_class = KeyCloakAuthentication

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4
