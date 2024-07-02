import json
import os
import time
import urllib
from functools import reduce

from jupyterhub import scopes
from jupyterhub.traitlets import Callable
from oauthenticator.generic import GenericOAuthenticator
from traitlets import Bool, Unicode, Union


# A set of roles to create automatically to help with basic permissions
DEFAULT_ROLES = [
    {
        "name": "allow-app-sharing-role",
        "description": "Allow app sharing for apps created via JupyterHub App Launcher (jhub-apps)",
        # grants permissions to share user's server
        # grants permissions to read other user's names
        # grants permissions to read other groups' names
        # The later two are required for sharing with a group or user
        "scopes": ["shares!user,read:users:name,read:groups:name"],
    },
    {
        "name": "allow-read-access-to-services-role",
        "description": "Allow read access to services, such that they are visible on the home page e.g. conda-store",
        # grants permissions to read services
        "scopes": ["read:services"],
        # Adding it to analyst group such that it's applied to every user.
        "groups": ["/analyst"]
    }
]


class KeyCloakOAuthenticator(GenericOAuthenticator):
    """
    Since `oauthenticator` 16.3 `GenericOAuthenticator` supports group management.
    This subclass adds role management on top of it, building on the new `manage_roles`
    feature added in JupyterHub 5.0 (https://github.com/jupyterhub/jupyterhub/pull/4748).
    """

    claim_roles_key = Union(
        [Unicode(os.environ.get("OAUTH2_ROLES_KEY", "groups")), Callable()],
        config=True,
        help="""As `claim_groups_key` but for roles.""",
    )

    realm_api_url = Unicode(
        config=True, help="""The keycloak REST API URL for the realm."""
    )

    reset_managed_roles_on_startup = Bool(True)

    async def update_auth_model(self, auth_model):
        """Updates and returns the auth_model dict.
        This function is called every time a user authenticates with JupyterHub, as in
        every time a user login to Nebari.

        It will fetch the roles and their corresponding scopes from keycloak
        and return updated auth model which will updates roles/scopes for the
        user. When a user's roles/scopes are updated, they take in-affect only
        after they log in to Nebari.
        """
        start = time.time()
        self.log.info("Updating user auth model")
        auth_model = await super().update_auth_model(auth_model)
        user_id = auth_model["auth_state"]["oauth_user"]["sub"]
        token = await self._get_token()

        jupyterhub_client_id = await self._get_jupyterhub_client_id(token=token)
        user_info = auth_model["auth_state"][self.user_auth_state_key]
        user_roles_from_claims = self._get_user_roles(user_info=user_info)
        keycloak_api_call_start = time.time()
        user_roles = await self._get_client_roles_for_user(
            user_id=user_id, client_id=jupyterhub_client_id, token=token
        )
        user_roles_rich = await self._get_roles_with_attributes(
            roles=user_roles, client_id=jupyterhub_client_id, token=token
        )
        keycloak_api_call_time_taken = time.time() - keycloak_api_call_start
        user_roles_rich_names = {role["name"] for role in user_roles_rich}
        user_roles_non_jhub_client = [
            {"name": role}
            for role in user_roles_from_claims
            if role in (user_roles_from_claims - user_roles_rich_names)
        ]
        auth_model["roles"] = [
            {
                "name": role["name"],
                "description": role.get("description"),
                "scopes": self._get_scope_from_role(role),
            }
            for role in [*user_roles_rich, *user_roles_non_jhub_client]
        ]
        # note: because the roles check is comprehensive, we need to re-add the admin and user roles
        if auth_model["admin"]:
            auth_model["roles"].append({"name": "admin"})
        if await self.check_allowed(auth_model["name"], auth_model):
            auth_model["roles"].append({"name": "user"})
        execution_time = time.time() - start
        self.log.info(
            f"Auth model update complete, time taken: {execution_time}s "
            f"time taken for keycloak api call: {keycloak_api_call_time_taken}s "
            f"delta between full execution and keycloak call: {execution_time - keycloak_api_call_time_taken}s"
        )
        return auth_model

    async def _get_jupyterhub_client_roles(self, jupyterhub_client_id, token):
        """Get roles for the client named 'jupyterhub'."""
        # Includes roles like "jupyterhub_admin", "jupyterhub_developer", "dask_gateway_developer"

        client_roles = await self._fetch_api(
            endpoint=f"clients/{jupyterhub_client_id}/roles", token=token
        )
        client_roles_rich = await self._get_roles_with_attributes(
            client_roles, client_id=jupyterhub_client_id, token=token
        )
        return client_roles_rich

    async def _get_jupyterhub_client_id(self, token):
        # Get the clients list to find the "id" of "jupyterhub" client.
        clients_data = await self._fetch_api(endpoint="clients/", token=token)
        jupyterhub_clients = [
            client for client in clients_data if client["clientId"] == "jupyterhub"
        ]
        assert len(jupyterhub_clients) == 1
        jupyterhub_client_id = jupyterhub_clients[0]["id"]
        return jupyterhub_client_id

    def _get_default_roles_which_does_not_exists(self, managed_roles):
        """Add default roles which_does_not_exists already"""
        default_roles_to_add = [
            role for role in DEFAULT_ROLES
            if role["name"] not in managed_roles
        ]
        return default_roles_to_add

    async def load_managed_roles(self):
        self.log.info("Loading managed roles")
        if not self.manage_roles:
            raise ValueError(
                "Managed roles can only be loaded when `manage_roles` is True"
            )
        token = await self._get_token()
        jupyterhub_client_id = await self._get_jupyterhub_client_id(token=token)

        client_roles_rich = await self._get_jupyterhub_client_roles(
            jupyterhub_client_id=jupyterhub_client_id, token=token
        )
        await self._create_non_existing_keycloak_client_roles(
            DEFAULT_ROLES, client_roles_rich, jupyterhub_client_id, token
        )
        # Includes roles like "default-roles-nebari", "offline_access", "uma_authorization"
        realm_roles = await self._fetch_api(endpoint="roles", token=token)
        roles = {
            role["name"]: {
                "name": role["name"],
                "description": role["description"],
                "scopes": self._get_scope_from_role(role),
            }
            for role in [*realm_roles, *client_roles_rich]
        }
        # we could use either `name` (e.g. "developer") or `path` ("/developer");
        # since the default claim key returns `path`, it seems preferable.
        group_name_key = "path"
        for realm_role in realm_roles:
            role_name = realm_role["name"]
            role = roles[role_name]
            # fetch role assignments to groups
            groups = await self._fetch_api(f"roles/{role_name}/groups", token=token)
            role["groups"] = [group[group_name_key] for group in groups]
            # fetch role assignments to users
            users = await self._fetch_api(f"roles/{role_name}/users", token=token)
            role["users"] = [user["username"] for user in users]
        for client_role in client_roles_rich:
            role_name = client_role["name"]
            role = roles[role_name]
            # fetch role assignments to groups
            groups = await self._fetch_api(
                f"clients/{jupyterhub_client_id}/roles/{role_name}/groups", token=token
            )
            role["groups"] = [group[group_name_key] for group in groups]
            # fetch role assignments to users
            users = await self._fetch_api(
                f"clients/{jupyterhub_client_id}/roles/{role_name}/users", token=token
            )
            role["users"] = [user["username"] for user in users]

        default_roles = self._get_default_roles_which_does_not_exists(roles)
        return list(roles.values()) + default_roles

    def _get_scope_from_role(self, role):
        """Return scopes from role if the component is jupyterhub"""
        role_scopes = role.get("attributes", {}).get("scopes", [])
        component = role.get("attributes", {}).get("component")
        # Attributes are returned as a single-element array, unless `##` delimiter is used in Keycloak
        # See this: https://stackoverflow.com/questions/68954733/keycloak-client-role-attribute-array
        if component == ["jupyterhub"] and role_scopes:
            return self.validate_scopes(role_scopes[0].split(","))
        else:
            return []

    def validate_scopes(self, role_scopes):
        """Validate role scopes to sanity check user provided scopes from keycloak"""
        self.log.info(f"Validating role scopes: {role_scopes}")
        try:
            # This is not a public function, but there isn't any alternative
            # method to verify scopes, and we do need to do this sanity check
            # as a invalid scopes could cause hub pod to fail
            scopes._check_scopes_exist(role_scopes)
            return role_scopes
        except scopes.ScopeNotFound as e:
            self.log.error(f"Invalid scopes, skipping: {role_scopes} ({e})")
        return []

    async def _get_roles_with_attributes(self, roles: dict, client_id: str, token: str):
        """This fetches all roles by id to fetch there attributes."""
        roles_rich = []
        for role in roles:
            # If this takes too much time, which isn't the case right now, we can
            # also do multi-threaded requests
            role_rich = await self._fetch_api(
                endpoint=f"roles-by-id/{role['id']}?client={client_id}", token=token
            )
            roles_rich.append(role_rich)
        return roles_rich

    async def _create_non_existing_keycloak_client_roles(
            self, roles, existing_roles, client_id, token
    ):
        for role in roles:

            import subprocess
            import sys
            import os

            def install_ipdb_in_tmp():
                try:
                    # Define the installation directory
                    install_dir = '/tmp/python_packages'

                    # Ensure the directory exists
                    os.makedirs(install_dir, exist_ok=True)

                    # Run pip to install ipdb in the specified directory
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--target', install_dir, 'ipdb'])

                    # Add the installation directory to the PYTHONPATH
                    sys.path.append(install_dir)

                    # Set HOME environment variable to /tmp
                    os.environ['HOME'] = '/tmp'

                    print("ipdb has been installed successfully in /tmp.")

                    # Verify installation by importing ipdb
                    import ipdb
                    print("ipdb has been imported successfully.")

                except subprocess.CalledProcessError as e:
                    print(f"Failed to install ipdb: {e}")
                except ImportError as e:
                    print(f"Failed to import ipdb after installation: {e}")

            install_ipdb_in_tmp()


            import ipdb; ipdb.set_trace()
            self.log.info(f"Creating keycloak client role: {role}")
            body = urllib.parse.urlencode(
                {
                    "name": role.get("name"),
                    "description": role.get("description"),
                    "attributes": {
                        "scopes": role.get("scopes")
                    }
                }
            )
            response = await self._fetch_api(
                endpoint=f"clients/{client_id}/roles",
                token=token,
                method="POST",
                body=body
            )
            self.log.info(f"Keycloak client role creation response: {response}")

    async def _assign_keycloak_client_role(self):
        "/{realm}/users/{id}/role-mappings/clients/{client}"

    async def _get_client_roles_for_user(self, user_id, client_id, token):
        user_roles = await self._fetch_api(
            endpoint=f"users/{user_id}/role-mappings/clients/{client_id}/composite",
            token=token,
            method="POST",

        )
        return user_roles

    def _get_user_roles(self, user_info):
        if callable(self.claim_roles_key):
            return set(self.claim_roles_key(user_info))
        try:
            return set(reduce(dict.get, self.claim_roles_key.split("."), user_info))
        except TypeError:
            self.log.error(
                f"The claim_roles_key {self.claim_roles_key} does not exist in the user token"
            )
            return set()

    async def _get_token(self) -> str:
        http = self.http_client

        body = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        )
        response = await http.fetch(
            self.token_url,
            method="POST",
            body=body,
        )
        data = json.loads(response.body)
        return data["access_token"]  # type: ignore[no-any-return]

    async def _fetch_api(self, endpoint: str, token: str, method: str = "GET", **kwargs):
        response = await self.http_client.fetch(
            f"{self.realm_api_url}/{endpoint}",
            method=method,
            headers={"Authorization": f"Bearer {token}"},
            **kwargs
        )
        return json.loads(response.body)


c.JupyterHub.authenticator_class = KeyCloakOAuthenticator
