import json
import logging
import re
import tempfile
import urllib
import urllib.parse
import urllib.request
from pathlib import Path

import requests
from conda_store_server import api, orm, schema
from conda_store_server.server.auth import GenericOAuthAuthentication
from conda_store_server.server.dependencies import get_conda_store
from conda_store_server.storage import S3Storage


def conda_store_config(path="/var/lib/conda-store/config.json"):
    with open(path) as f:
        return json.load(f)


config = conda_store_config()

# ==================================
#      conda-store settings
# ==================================
c.CondaStore.storage_class = S3Storage
c.CondaStore.store_directory = "/home/conda/"
c.CondaStore.database_url = f"postgresql+psycopg2://{config['postgres-username']}:{config['postgres-password']}@{config['postgres-service']}/conda-store"
c.CondaStore.redis_url = (
    f"redis://:{config['redis-password']}@{config['redis-service']}:6379/0"
)
c.CondaStore.default_uid = 1000
c.CondaStore.default_gid = 100
c.CondaStore.default_permissions = "555"
c.CondaStore.conda_included_packages = ["ipykernel"]

c.S3Storage.internal_endpoint = f"{config['minio-service']}:9000"
c.S3Storage.internal_secure = False
c.S3Storage.external_endpoint = f"{config['external-url']}:9080"
c.S3Storage.external_secure = True
c.S3Storage.access_key = config["minio-username"]
c.S3Storage.secret_key = config["minio-password"]
c.S3Storage.region = "us-east-1"  # minio region default
c.S3Storage.bucket_name = "conda-store"

c.CondaStore.default_namespace = "global"
c.CondaStore.filesystem_namespace = config["default-namespace"]
c.CondaStore.conda_allowed_channels = []  # allow all channels
c.CondaStore.conda_indexed_channels = [
    "main",
    "conda-forge",
    "https://repo.anaconda.com/pkgs/main",
]
c.RBACAuthorizationBackend.role_mappings_version = 2

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
c.CondaStoreServer.behind_proxy = True
# This MUST start with `/`
c.CondaStoreServer.url_prefix = "/conda-store"

# ==================================
#         auth settings
# ==================================

c.GenericOAuthAuthentication.access_token_url = config["openid-config"]["token_url"]
c.GenericOAuthAuthentication.authorize_url = config["openid-config"][
    "authentication_url"
]
c.GenericOAuthAuthentication.user_data_url = config["openid-config"]["userinfo_url"]
c.GenericOAuthAuthentication.oauth_callback_url = (
    f"https://{config['external-url']}/conda-store/oauth_callback"
)
c.GenericOAuthAuthentication.client_id = config["openid-config"]["client_id"]
c.GenericOAuthAuthentication.client_secret = config["openid-config"]["client_secret"]
c.GenericOAuthAuthentication.access_scope = "profile"
c.GenericOAuthAuthentication.user_data_key = "preferred_username"
c.GenericOAuthAuthentication.tls_verify = False


class KeyCloakAuthentication(GenericOAuthAuthentication):
    conda_store_api_url = f"https://{config['external-url']}/conda-store/api/v1"
    access_token_url = config["openid-config"]["token_url"]
    realm_api_url = config["realm_api_url"]
    service_account_token = config["service-tokens-mapping"][
        "conda-store-service-account"
    ]
    conda_store_role_permissions_order = ["viewer", "developer", "admin"]

    def disable_ssl_verify_ctx(self):
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _get_conda_store_client_id(self, token):
        # Get the clients list to find the "id" of "conda-store" client.
        self.log.info("Getting conda store client id")
        clients_data = self._fetch_api(endpoint="clients/", token=token)
        conda_store_clients = [
            client for client in clients_data if client["clientId"] == "conda_store"
        ]
        self.log.info(f"conda store clients: {conda_store_clients}")
        assert len(conda_store_clients) == 1
        conda_store_client_id = conda_store_clients[0]["id"]
        return conda_store_client_id

    async def delete_conda_store_roles(self, request, namespace, username):
        self.log.info(
            f"Delete all conda-store roles on namespace: {namespace} for user: {username}"
        )
        conda_store = await get_conda_store(request)
        with conda_store.session_factory() as db:
            api.delete_namespace_role(db, namespace, other=username)
            db.commit()

    async def create_conda_store_role(self, request, namespace, username, role):
        self.log.info(
            f"Creating conda-store roles on namespace: {namespace} for user: {username}"
        )
        conda_store = await get_conda_store(request)
        with conda_store.session_factory() as db:
            api.create_namespace_role(db, namespace, username, role)
            db.commit()

    def _get_token(self) -> str:
        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        )
        # urllib
        req = urllib.request.Request(self.access_token_url, data=body.encode())
        response = urllib.request.urlopen(req, context=self.disable_ssl_verify_ctx())
        data = json.loads(response.read())
        return data["access_token"]  # type: ignore[no-any-return]

    def _fetch_api(self, endpoint: str, token: str):
        req = urllib.request.Request(
            f"{self.realm_api_url}/{endpoint}",
            method="GET",
            headers={"Authorization": f"Bearer {token}"},
        )
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(
            req, context=self.disable_ssl_verify_ctx()
        ) as response:
            data = json.loads(response.read())
        return data

    async def remove_current_bindings(self, request, username):
        """Remove current roles for the user to make sure only the roles defined in
        keycloak are applied:
        - to avoid inconsistency in user roles
        - single source of truth
        - roles that are added in keycloak and then later removed from keycloak are actually removed from conda-store.
        """
        entity_bindings = self.get_current_entity_bindings(username)
        self.log.info("Remove current role bindings for the user")
        for entity, role in entity_bindings.items():
            if entity not in {"default/*", "filesystem/*"}:
                namespace = entity.split("/")[0]
                self.log.info(
                    f"Removing current role {role} on namespace {namespace} "
                    f"for user {username}"
                )
                await self.delete_conda_store_roles(request, namespace, username)

    async def apply_roles_from_keycloak(self, request, user_data):
        token = self._get_token()
        conda_store_client_id = self._get_conda_store_client_id(token)
        conda_store_client_roles = self.get_conda_store_client_roles_for_user(
            user_data["sub"], conda_store_client_id, token
        )
        await self.remove_current_bindings(request, user_data["preferred_username"])
        await self._apply_conda_store_roles_from_keycloak(
            request, conda_store_client_roles, user_data["preferred_username"]
        )

    def is_valid_conda_store_role(self, keycloak_role):
        conda_store_role, namespace = self._get_permissions_from_keycloak_role(
            keycloak_role
        )
        if conda_store_role not in self.conda_store_role_permissions_order:
            self.log.info(
                f"role {conda_store_role} not valid as not one of {self.conda_store_role_permissions_order}"
            )
            return False
        if not namespace or (not conda_store_role):
            self.log(f"Not a valid conda store role: {conda_store_role}")
            return False
        return True

    def filter_duplicate_namespace_roles_with_max_permissions(self, role_permissions):
        """Filter duplicate roles in keycloak such that to apply only the one with the highest
        permissions.

        Example:
            role 1: namespace: foo, role: viewer
            role 2: namespace: foo, role: admin
        We need to apply only the role 2 as that one has higher permissions.
        """
        self.log.info("Filtering duplicate roles for same namespace")
        namespace_role_mapping = {}
        for role_permission in role_permissions:
            namespace = role_permission.get("namespace")
            new_role = role_permission.get("role")

            existing_role = namespace_role_mapping.get(namespace)
            if not existing_role:
                # Add if not already added
                namespace_role_mapping[namespace] = new_role
            else:
                # Only add if the permissions of this role is higher than existing
                new_role_priority = self.conda_store_role_permissions_order.index(
                    new_role
                )
                existing_role_priority = self.conda_store_role_permissions_order.index(
                    existing_role
                )
                if new_role_priority > existing_role_priority:
                    namespace_role_mapping[namespace] = new_role
        return namespace_role_mapping

    def parse_role_and_namespace(self, text):
        # The regex pattern
        pattern = r"^(\w+)!namespace=([^!]+)$"

        # Perform the regex search
        match = re.search(pattern, text)

        # Extract the permission and namespace if there is a match
        if match:
            role = match.group(1)
            namespace = match.group(2)
            return {"role": role, "namespace": namespace}
        else:
            return None

    def _parse_scope(self, scopes):
        """Parsed scopes from keycloak role's attribute and returns a list of role/namespace
        if scopes' syntax is valid otherwise return []

        Example:
            Given scopes as "viewer!namespace=scipy,admin!namespace=pycon", the function will
            return [{"role": "viewer", "namespace": "scipy"}, {"role": "admin", "namespace": "pycon"}]
        """
        if not scopes:
            self.log.info(f"No scope found: {scopes}, skipping role")
            return []
        scope_list = scopes.split(",")
        parsed_scopes = []
        self.log.info(f"Scopes to parse: {scope_list}")
        for scope_text in scope_list:
            parsed_scope = self.parse_role_and_namespace(scope_text)
            parsed_scopes.append(parsed_scope)
            if not parsed_scope:
                self.log.info(f"Unable to parse: {scope_text}, skipping keycloak role")
                return []
        return parsed_scopes

    def _get_permissions_from_keycloak_role(self, keycloak_role):
        self.log.info(f"Getting permissions from keycloak role: {keycloak_role}")
        role_attributes = keycloak_role["attributes"]
        # scopes returns a list with a value say ["viewer!namespace=pycon,developer!namespace=scipy"]
        scopes = role_attributes.get("scopes", [""])[0]
        return self._parse_scope(scopes)

    async def _apply_conda_store_roles_from_keycloak(
        self, request, conda_store_client_roles, username
    ):
        self.log.info(
            f"Apply conda store roles from keycloak roles: {conda_store_client_roles}, user: {username}"
        )
        role_permissions = []
        for conda_store_client_role in conda_store_client_roles:
            role_permissions += self._get_permissions_from_keycloak_role(
                conda_store_client_role
            )

        self.log.info("Filtering duplicate namespace role for max permissions")
        filtered_role_permissions = (
            self.filter_duplicate_namespace_roles_with_max_permissions(role_permissions)
        )
        self.log.info(f"Final role permissions to apply: {filtered_role_permissions}")
        for namespace, role in filtered_role_permissions.items():
            if namespace.lower() == username.lower():
                self.log.info("Role for given user's namespace, skipping")
                continue
            try:
                await self.delete_conda_store_roles(request, namespace, username)
                await self.create_conda_store_role(request, namespace, username, role)
            except ValueError as e:
                self.log.error(
                    f"Failed to add permissions for namespace: {namespace} to user: {username}"
                )
                self.log.exception(e)

    def _get_roles_with_attributes(self, roles: dict, client_id: str, token: str):
        """This fetches all roles by id to fetch their attributes."""
        roles_rich = []
        for role in roles:
            # If this takes too much time, which isn't the case right now, we can
            # also do multi-threaded requests
            role_rich = self._fetch_api(
                endpoint=f"roles-by-id/{role['id']}?client={client_id}", token=token
            )
            roles_rich.append(role_rich)
        return roles_rich

    def get_conda_store_client_roles_for_user(
        self, user_id, conda_store_client_id, token
    ):
        """Get roles for the client named 'jupyterhub'."""
        # Includes roles like "jupyterhub_admin", "jupyterhub_developer", "dask_gateway_developer"
        self.log.info(
            f"get conda store client roles for user: {user_id}, conda_store_client_id: {conda_store_client_id}"
        )
        user_roles = self._fetch_api(
            endpoint=f"users/{user_id}/role-mappings/clients/{conda_store_client_id}/composite",
            token=token,
        )
        client_roles_rich = self._get_roles_with_attributes(
            user_roles, client_id=conda_store_client_id, token=token
        )
        self.log.info(f"conda store client roles: {client_roles_rich}")
        return client_roles_rich

    def get_current_entity_bindings(self, username):
        entity = schema.AuthenticationToken(
            primary_namespace=username, role_bindings={}
        )
        self.log.info(f"entity: {entity}")
        entity_bindings = self.authorization.get_entity_bindings(entity)
        self.log.info(f"current entity_bindings: {entity_bindings}")
        return entity_bindings

    def _override_logger(self):
        """The default logger is not very useful, and it doesn't have any formatting"""
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)9s %(name)s:%(lineno)4s: %(message)s"
        )
        for handler in self.log.handlers:
            handler.setFormatter(formatter)

    async def authenticate(self, request):
        self._override_logger()
        oauth_access_token = self._get_oauth_token(request)
        # self.log.info(f"oauth_access_token: {oauth_access_token}")
        if oauth_access_token is None:
            return None  # authentication failed

        response = requests.get(
            self.user_data_url,
            headers={"Authorization": f"Bearer {oauth_access_token}"},
            verify=self.tls_verify,
        )
        response.raise_for_status()
        user_data = response.json()
        username = user_data["preferred_username"]

        try:
            await self.apply_roles_from_keycloak(request, user_data=user_data)
        except Exception as e:
            self.log.error("Adding roles from keycloak failed")
            self.log.exception(e)

        # superadmin gets access to everything
        if "conda_store_superadmin" in user_data.get("roles", []):
            return schema.AuthenticationToken(
                primary_namespace=username,
                role_bindings={"*/*": {"admin"}},
            )

        # Remove this after next release (2026.7.1), keeping it for now for backwards compatibility
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
        default_namespace = config["default-namespace"]
        self.log.info(f"default_namespace: {default_namespace}")
        namespaces = {username, "global", default_namespace}
        self.log.info(f"namespaces: {namespaces}")
        role_bindings = {
            f"{username}/*": {"admin"},
            f"{default_namespace}/*": {"viewer"},
            "global/*": roles,
        }

        for group in user_data.get("groups", []):
            # Use only the base name of Keycloak groups
            group_name = Path(group).name
            namespaces.add(group_name)
            role_bindings[f"{group_name}/*"] = roles

        conda_store = await get_conda_store(request)
        with conda_store.session_factory() as db:
            for namespace in namespaces:
                _namespace = api.get_namespace(db, name=namespace)
                if _namespace is None:
                    db.add(orm.Namespace(name=namespace))
                    db.commit()

        return schema.AuthenticationToken(
            primary_namespace=username,
            role_bindings=role_bindings,
        )


c.CondaStoreServer.authentication_class = KeyCloakAuthentication
c.AuthenticationBackend.predefined_tokens = {
    service_token: service_permissions
    for service_token, service_permissions in config["service-tokens"].items()
}

# ==================================
#         worker settings
# ==================================
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4

# Template used to form the directory for symlinking conda environment builds.
c.CondaStore.environment_directory = "/home/conda/{namespace}/envs/{namespace}-{name}"

# extra-settings to apply simply as `c.Class.key = value`
conda_store_settings = config["extra-settings"]
for classname, attributes in conda_store_settings.items():
    for attribute, value in attributes.items():
        setattr(getattr(c, classname), attribute, value)

# run arbitrary python code
# compiling makes debugging easier: https://stackoverflow.com/a/437857
extra_config_filename = Path(tempfile.gettempdir()) / "extra-config.py"
extra_config = config.get("extra-config", "")
with open(extra_config_filename, "w") as f:
    f.write(extra_config)
exec(compile(source=extra_config, filename=extra_config_filename, mode="exec"))
