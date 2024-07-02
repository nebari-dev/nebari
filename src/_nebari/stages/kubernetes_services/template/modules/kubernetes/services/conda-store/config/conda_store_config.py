import dataclasses
import json
import logging
import re
import tempfile
import typing
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
c.CondaStoreServer.log_format = (
    "%(asctime)s %(levelname)9s %(name)s:%(lineno)4s: %(message)s"
)
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

CONDA_STORE_ROLE_PERMISSIONS_ORDER = ["viewer", "developer", "admin"]


@dataclasses.dataclass
class CondaStoreNamespaceRole:
    namespace: str
    role: str


@dataclasses.dataclass
class KeyCloakCondaStoreRoleScopes:
    scopes: str
    log: logging.Logger

    def _validate_role(self, role):
        valid = role in CONDA_STORE_ROLE_PERMISSIONS_ORDER
        self.log.info(f"role: {role} is {'valid' if valid else 'invalid'}")
        return valid

    def parse_role_and_namespace(
        self, text
    ) -> typing.Optional[CondaStoreNamespaceRole]:
        # The regex pattern
        pattern = r"^(\w+)!namespace=([^!]+)$"

        # Perform the regex search
        match = re.search(pattern, text)

        # Extract the permission and namespace if there is a match
        if match and self._validate_role(match.group(1)):
            return CondaStoreNamespaceRole(
                namespace=match.group(2), role=match.group(1)
            )
        else:
            return None

    def parse_scope(self) -> typing.List[CondaStoreNamespaceRole]:
        """Parsed scopes from keycloak role's attribute and returns a list of role/namespace
        if scopes' syntax is valid otherwise return []

        Example:
            Given scopes as "viewer!namespace=scipy,admin!namespace=pycon", the function will
            return [{"role": "viewer", "namespace": "scipy"}, {"role": "admin", "namespace": "pycon"}]
        """
        if not self.scopes:
            self.log.info(f"No scope found: {self.scopes}, skipping role")
            return []
        scope_list = self.scopes.split(",")
        parsed_scopes = []
        self.log.info(f"Scopes to parse: {scope_list}")
        for scope_text in scope_list:
            parsed_scope = self.parse_role_and_namespace(scope_text)
            parsed_scopes.append(parsed_scope)
            if not parsed_scope:
                self.log.info(f"Unable to parse: {scope_text}, skipping keycloak role")
                return []
        return parsed_scopes


class KeyCloakAuthentication(GenericOAuthAuthentication):
    conda_store_api_url = f"https://{config['external-url']}/conda-store/api/v1"
    access_token_url = config["token_url_internal"]
    realm_api_url = config["realm_api_url_internal"]
    service_account_token = config["service-tokens-mapping"][
        "conda-store-service-account"
    ]

    def _get_conda_store_client_id(self, token: str) -> str:
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

    async def _delete_conda_store_roles(self, request, namespace: str, username: str):
        self.log.info(
            f"Delete all conda-store roles on namespace: {namespace} for user: {username}"
        )
        conda_store = await get_conda_store(request)
        with conda_store.session_factory() as db:
            api.delete_namespace_role(db, namespace, other=username)
            db.commit()

    async def _create_conda_store_role(
        self, request, namespace_role: CondaStoreNamespaceRole, username: str
    ):
        self.log.info(
            f"Creating conda-store roles on namespace: {namespace_role.namespace} for user: {username}"
        )
        conda_store = await get_conda_store(request)
        with conda_store.session_factory() as db:
            api.create_namespace_role(
                db, namespace_role.namespace, username, namespace_role.role
            )
            db.commit()

    def _get_keycloak_token(self) -> str:
        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        )
        self.log.info(f"Getting token from access token url: {self.access_token_url}")
        req = urllib.request.Request(self.access_token_url, data=body.encode())
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        return data["access_token"]  # type: ignore[no-any-return]

    def _fetch_api(self, endpoint: str, token: str):
        request_url = f"{self.realm_api_url}/{endpoint}"
        req = urllib.request.Request(
            request_url,
            method="GET",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.log.info(f"Making request to: {request_url}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
        return data

    async def _remove_current_bindings(self, request, username):
        """Remove current roles for the user to make sure only the roles defined in
        keycloak are applied:
        - to avoid inconsistency in user roles
        - single source of truth
        - roles that are added in keycloak and then later removed from keycloak are actually removed from conda-store.
        """
        entity_bindings = self._get_current_entity_bindings(username)
        self.log.info("Remove current role bindings for the user")
        for entity, role in entity_bindings.items():
            if entity not in {"default/*", "filesystem/*"}:
                namespace = entity.split("/")[0]
                self.log.info(
                    f"Removing current role {role} on namespace {namespace} "
                    f"for user {username}"
                )
                await self._delete_conda_store_roles(request, namespace, username)

    async def _apply_roles_from_keycloak(self, request, user_data):
        token = self._get_keycloak_token()
        conda_store_client_id = self._get_conda_store_client_id(token)
        conda_store_client_roles = self._get_conda_store_client_roles_for_user(
            user_data["sub"], conda_store_client_id, token
        )
        await self._remove_current_bindings(request, user_data["preferred_username"])
        await self._apply_conda_store_roles_from_keycloak(
            request, conda_store_client_roles, user_data["preferred_username"]
        )

    def _filter_duplicate_namespace_roles_with_max_permissions(
        self, namespace_roles: typing.List[CondaStoreNamespaceRole]
    ):
        """Filter duplicate roles in keycloak such that to apply only the one with the highest
        permissions.

        Example:
            role 1: namespace: foo, role: viewer
            role 2: namespace: foo, role: admin
        We need to apply only the role 2 as that one has higher permissions.
        """
        self.log.info("Filtering duplicate roles for same namespace")
        namespace_role_mapping: typing.Dict[str:CondaStoreNamespaceRole] = {}
        for namespace_role in namespace_roles:
            namespace = namespace_role.namespace
            new_role = namespace_role.role

            existing_role: CondaStoreNamespaceRole = namespace_role_mapping.get(
                namespace
            )
            if not existing_role:
                # Add if not already added
                namespace_role_mapping[namespace] = namespace_role
            else:
                # Only add if the permissions of this role is higher than existing
                new_role_priority = CONDA_STORE_ROLE_PERMISSIONS_ORDER.index(new_role)
                existing_role_priority = CONDA_STORE_ROLE_PERMISSIONS_ORDER.index(
                    existing_role.role
                )
                if new_role_priority > existing_role_priority:
                    namespace_role_mapping[namespace] = new_role
        return list(namespace_role_mapping.values())

    def _get_permissions_from_keycloak_role(
        self, keycloak_role
    ) -> typing.List[CondaStoreNamespaceRole]:
        self.log.info(f"Getting permissions from keycloak role: {keycloak_role}")
        role_attributes = keycloak_role["attributes"]
        # scopes returns a list with a value say ["viewer!namespace=pycon,developer!namespace=scipy"]
        scopes = role_attributes.get("scopes", [""])[0]
        k_cstore_scopes = KeyCloakCondaStoreRoleScopes(scopes=scopes, log=self.log)
        return k_cstore_scopes.parse_scope()

    async def _apply_conda_store_roles_from_keycloak(
        self, request, conda_store_client_roles, username
    ):
        self.log.info(
            f"Apply conda store roles from keycloak roles: {conda_store_client_roles}, user: {username}"
        )
        role_permissions: typing.List[CondaStoreNamespaceRole] = []
        for conda_store_client_role in conda_store_client_roles:
            role_permissions += self._get_permissions_from_keycloak_role(
                conda_store_client_role
            )

        self.log.info("Filtering duplicate namespace role for max permissions")
        filtered_namespace_role: typing.List[CondaStoreNamespaceRole] = (
            self._filter_duplicate_namespace_roles_with_max_permissions(
                role_permissions
            )
        )
        self.log.info(f"Final role permissions to apply: {filtered_namespace_role}")
        for namespace_role in filtered_namespace_role:
            if namespace_role.namespace.lower() == username.lower():
                self.log.info("Role for given user's namespace, skipping")
                continue
            try:
                await self._delete_conda_store_roles(
                    request, namespace_role.namespace, username
                )
                await self._create_conda_store_role(request, namespace_role, username)
            except ValueError as e:
                self.log.error(
                    f"Failed to add permissions for namespace: {namespace_role.namespace} to user: {username}"
                )
                self.log.exception(e)

    def _get_keycloak_conda_store_roles_with_attributes(
        self, roles: dict, client_id: str, token: str
    ):
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

    def _get_conda_store_client_roles_for_user(
        self, user_id, conda_store_client_id, token
    ):
        """Get roles for the client named 'conda-store' for the given user_id."""
        self.log.info(
            f"Get conda store client roles for user: {user_id}, conda_store_client_id: {conda_store_client_id}"
        )
        user_roles = self._fetch_api(
            endpoint=f"users/{user_id}/role-mappings/clients/{conda_store_client_id}/composite",
            token=token,
        )
        client_roles_rich = self._get_keycloak_conda_store_roles_with_attributes(
            user_roles, client_id=conda_store_client_id, token=token
        )
        self.log.info(f"conda store client roles: {client_roles_rich}")
        return client_roles_rich

    def _get_current_entity_bindings(self, username):
        entity = schema.AuthenticationToken(
            primary_namespace=username, role_bindings={}
        )
        self.log.info(f"entity: {entity}")
        entity_bindings = self.authorization.get_entity_bindings(entity)
        self.log.info(f"current entity_bindings: {entity_bindings}")
        return entity_bindings

    async def authenticate(self, request):
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
        username = user_data["preferred_username"]

        try:
            await self._apply_roles_from_keycloak(request, user_data=user_data)
        except Exception as e:
            self.log.error("Adding roles from keycloak failed")
            self.log.exception(e)

        # superadmin gets access to everything
        if "conda_store_superadmin" in user_data.get("roles", []):
            return schema.AuthenticationToken(
                primary_namespace=username,
                role_bindings={"*/*": {"admin"}},
            )

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
