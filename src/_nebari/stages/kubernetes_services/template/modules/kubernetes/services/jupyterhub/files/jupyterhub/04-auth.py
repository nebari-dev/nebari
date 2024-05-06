import json
import os
import urllib
from functools import reduce

from jupyterhub.traitlets import Callable
from oauthenticator.generic import GenericOAuthenticator
from traitlets import Bool, Unicode, Union


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
        auth_model = await super().update_auth_model(auth_model)
        user_info = auth_model["auth_state"][self.user_auth_state_key]
        user_roles = self._get_user_roles(user_info)
        auth_model["roles"] = [{"name": role_name} for role_name in user_roles]
        # note: because the roles check is comprehensive, we need to re-add the admin and user roles
        if auth_model["admin"]:
            auth_model["roles"].append({"name": "admin"})
        if self.check_allowed(auth_model["name"], auth_model):
            auth_model["roles"].append({"name": "user"})
        return auth_model

    async def load_managed_roles(self):
        if not self.manage_roles:
            raise ValueError(
                "Managed roles can only be loaded when `manage_roles` is True"
            )
        token = await self._get_token()

        # Get the clients list to find the "id" of "jupyterhub" client.
        clients_data = await self._fetch_api(endpoint="clients/", token=token)
        jupyterhub_clients = [
            client for client in clients_data if client["clientId"] == "jupyterhub"
        ]
        assert len(jupyterhub_clients) == 1
        jupyterhub_client_id = jupyterhub_clients[0]["id"]

        # Includes roles like "jupyterhub_admin", "jupyterhub_developer", "dask_gateway_developer"
        client_roles = await self._fetch_api(
            endpoint=f"clients/{jupyterhub_client_id}/roles", token=token
        )
        # Includes roles like "default-roles-nebari", "offline_access", "uma_authorization"
        realm_roles = await self._fetch_api(endpoint="roles", token=token)
        roles = {
            role["name"]: {"name": role["name"], "description": role["description"]}
            for role in [*realm_roles, *client_roles]
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
        for client_role in client_roles:
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

        return list(roles.values())

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

    async def _fetch_api(self, endpoint: str, token: str):
        response = await self.http_client.fetch(
            f"{self.realm_api_url}/{endpoint}",
            method="GET",
            headers={"Authorization": f"Bearer {token}"},
        )
        return json.loads(response.body)


c.JupyterHub.authenticator_class = KeyCloakOAuthenticator
