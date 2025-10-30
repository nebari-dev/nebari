"""Helper class for Keycloak API interactions."""

import base64
import json
import os
import time
from http import HTTPStatus

import requests

TIMEOUT = int(os.getenv("KEYCLOAK_TIMEOUT", "10"))


def decode_jwt_token(token: str) -> dict:
    """Decode a JWT token without verification (for testing purposes).
    ******************************
    DO NOT USE THIS FOR PRODUCTION
    ******************************
    Parameters
    ----------
    token : str
        The JWT token to decode

    Returns
    -------
    dict
        The decoded token payload
    """
    # Split the token into parts
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format")

    # Decode the payload (second part)
    payload = parts[1]
    # Add padding if needed
    padding = len(payload) % 4
    if padding:
        payload += "=" * (4 - padding)

    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)


class KeycloakAPI:
    """
    Helper class for making requests to Keycloak.
    Handles OAuth2 authentication flows.
    """

    def __init__(
        self,
        base_url: str,
        realm: str,
        client_id: str,
        username: str = None,
        password: str = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize Keycloak API client.

        Parameters
        ----------
        base_url : str
            Base URL for Keycloak (e.g., "https://example.com/auth")
        realm : str
            Keycloak realm name
        client_id : str
            OAuth2 client ID
        username : str, optional
            Username for authentication
        password : str, optional
            Password for authentication
        verify_ssl : bool
            Whether to verify SSL certificates
        """
        self.verify_ssl = verify_ssl
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_type = None
        self.token_expires_at = None

        # Authenticate if credentials provided
        if username and password:
            self.authenticate()

    def _get_token_url(self) -> str:
        """Construct the token endpoint URL."""
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

    def authenticate(self, username: str = None, password: str = None) -> dict:
        """Authenticate with Keycloak using username and password.

        Parameters
        ----------
        username : str, optional
            Username to authenticate with (uses instance username if not provided)
        password : str, optional
            Password to authenticate with (uses instance password if not provided)

        Returns
        -------
        dict
            Token response containing access_token, refresh_token, etc.
        """
        username = username or self.username
        password = password or self.password

        if not username or not password:
            raise ValueError("Username and password are required for authentication")

        token_url = self._get_token_url()

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "username": username,
            "password": password,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            token_url,
            data=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        self.token_type = token_data.get("token_type")

        # Track token expiration (default to 5 minutes if not provided)
        expires_in = token_data.get("expires_in", 300)
        self.token_expires_at = time.time() + expires_in

        return token_data

    def refresh_access_token(self) -> dict:
        """Refresh the access token using the refresh token.

        Returns
        -------
        dict
            Token response containing new access_token and refresh_token

        Raises
        ------
        ValueError
            If no refresh token is available
        requests.exceptions.HTTPError
            If the refresh request fails (e.g., refresh token expired)
        """
        if not self.refresh_token:
            # If we have username/password, re-authenticate instead
            if self.username and self.password:
                return self.authenticate()
            raise ValueError(
                "No refresh token available and no credentials for re-authentication"
            )

        token_url = self._get_token_url()

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            token_url,
            data=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=TIMEOUT,
        )

        # If refresh fails and we have credentials, try to re-authenticate
        if response.status_code == HTTPStatus.BAD_REQUEST and self.username and self.password:
            return self.authenticate()

        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        self.token_type = token_data.get("token_type")

        # Update token expiration
        expires_in = token_data.get("expires_in", 300)
        self.token_expires_at = time.time() + expires_in

        return token_data

    def _get_admin_url(self, endpoint: str) -> str:
        """Construct an admin API endpoint URL.

        Parameters
        ----------
        endpoint : str
            The admin endpoint path (e.g., "users", "users/{id}")

        Returns
        -------
        str
            Full URL for the admin endpoint
        """
        return f"{self.base_url}/admin/realms/{self.realm}/{endpoint}"

    def _make_admin_request(
        self,
        endpoint: str,
        method: str = "GET",
        json_data: dict = None,
        timeout: int = TIMEOUT,
    ) -> requests.Response:
        """Make an authenticated request to the Keycloak admin API.

        Parameters
        ----------
        endpoint : str
            The admin endpoint path
        method : str
            HTTP method (GET, POST, PUT, DELETE)
        json_data : dict, optional
            JSON data to send in the request body
        timeout : int
            Request timeout in seconds

        Returns
        -------
        requests.Response
            Response from the admin API
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Auto-refresh token if expired or expiring soon (30 second buffer)
        if self.token_expires_at and time.time() > (self.token_expires_at - 30):
            self.refresh_access_token()

        url = self._get_admin_url(endpoint)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method,
            url,
            json=json_data,
            headers=headers,
            verify=self.verify_ssl,
            timeout=timeout,
        )

        return response

    def create_user(self, user_data: dict) -> requests.Response:
        """Create a new user in Keycloak.

        Parameters
        ----------
        user_data : dict
            User data including username, email, firstName, lastName, etc.
            Example: {"username": "testuser", "email": "test@example.com",
                     "enabled": True, "firstName": "Test", "lastName": "User"}

        Returns
        -------
        requests.Response
            Response from the create user request
        """
        return self._make_admin_request("users", method="POST", json_data=user_data)

    def get_users(self, username: str = None) -> requests.Response:
        """Get users from Keycloak.

        Parameters
        ----------
        username : str, optional
            Filter users by exact username match

        Returns
        -------
        requests.Response
            Response containing list of users
        """
        endpoint = "users"
        if username:
            endpoint = f"users?username={username}"
        return self._make_admin_request(endpoint)

    def get_user_by_id(self, user_id: str) -> requests.Response:
        """Get a specific user by ID.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID

        Returns
        -------
        requests.Response
            Response containing user data
        """
        return self._make_admin_request(f"users/{user_id}")

    def update_user(self, user_id: str, user_data: dict) -> requests.Response:
        """Update a user in Keycloak.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        user_data : dict
            User data to update (partial updates supported)

        Returns
        -------
        requests.Response
            Response from the update request
        """
        return self._make_admin_request(
            f"users/{user_id}", method="PUT", json_data=user_data
        )

    def delete_user(self, user_id: str) -> requests.Response:
        """Delete a user from Keycloak.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID to delete

        Returns
        -------
        requests.Response
            Response from the delete request
        """
        return self._make_admin_request(f"users/{user_id}", method="DELETE")

    def create_client(self, client_data: dict) -> requests.Response:
        """Create a new client in Keycloak.

        Parameters
        ----------
        client_data : dict
            Client data including clientId, protocol, publicClient, etc.
            Example: {"clientId": "test-client", "enabled": True,
                     "publicClient": False, "protocol": "openid-connect"}

        Returns
        -------
        requests.Response
            Response from the create client request
        """
        return self._make_admin_request("clients", method="POST", json_data=client_data)

    def get_clients(self, client_id: str = None) -> requests.Response:
        """Get clients from Keycloak.

        Parameters
        ----------
        client_id : str, optional
            Filter clients by clientId (not the internal ID)

        Returns
        -------
        requests.Response
            Response containing list of clients
        """
        endpoint = "clients"
        if client_id:
            endpoint = f"clients?clientId={client_id}"
        return self._make_admin_request(endpoint)

    def get_client_by_id(self, id: str) -> requests.Response:
        """Get a specific client by internal ID.

        Parameters
        ----------
        id : str
            The Keycloak client internal ID (not clientId)

        Returns
        -------
        requests.Response
            Response containing client data
        """
        return self._make_admin_request(f"clients/{id}")

    def update_client(self, id: str, client_data: dict) -> requests.Response:
        """Update a client in Keycloak.

        Parameters
        ----------
        id : str
            The Keycloak client internal ID
        client_data : dict
            Client data to update (partial updates supported)

        Returns
        -------
        requests.Response
            Response from the update request
        """
        return self._make_admin_request(
            f"clients/{id}", method="PUT", json_data=client_data
        )

    def delete_client(self, id: str) -> requests.Response:
        """Delete a client from Keycloak.

        Parameters
        ----------
        id : str
            The Keycloak client internal ID to delete

        Returns
        -------
        requests.Response
            Response from the delete request
        """
        return self._make_admin_request(f"clients/{id}", method="DELETE")

    def reset_user_password(
        self, user_id: str, password: str, temporary: bool = False
    ) -> requests.Response:
        """Reset a user's password.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        password : str
            The new password
        temporary : bool
            Whether the password is temporary (user must change on next login)

        Returns
        -------
        requests.Response
            Response from the password reset request
        """
        password_data = {"type": "password", "value": password, "temporary": temporary}
        return self._make_admin_request(
            f"users/{user_id}/reset-password", method="PUT", json_data=password_data
        )

    def get_client_secret(self, id: str) -> requests.Response:
        """Get the secret for a confidential client.

        Parameters
        ----------
        id : str
            The Keycloak client internal ID

        Returns
        -------
        requests.Response
            Response containing the client secret
        """
        return self._make_admin_request(f"clients/{id}/client-secret")

    def regenerate_client_secret(self, id: str) -> requests.Response:
        """Regenerate the secret for a confidential client.

        Parameters
        ----------
        id : str
            The Keycloak client internal ID

        Returns
        -------
        requests.Response
            Response containing the new client secret
        """
        return self._make_admin_request(f"clients/{id}/client-secret", method="POST")

    def create_realm_role(self, role_data: dict) -> requests.Response:
        """Create a new realm role.

        Parameters
        ----------
        role_data : dict
            Role data including name and description
            Example: {"name": "test-role", "description": "Test role"}

        Returns
        -------
        requests.Response
            Response from the create role request
        """
        return self._make_admin_request("roles", method="POST", json_data=role_data)

    def get_realm_roles(self) -> requests.Response:
        """Get all realm roles.

        Returns
        -------
        requests.Response
            Response containing list of realm roles
        """
        return self._make_admin_request("roles")

    def get_realm_role_by_name(self, role_name: str) -> requests.Response:
        """Get a specific realm role by name.

        Parameters
        ----------
        role_name : str
            The role name

        Returns
        -------
        requests.Response
            Response containing role data
        """
        return self._make_admin_request(f"roles/{role_name}")

    def delete_realm_role(self, role_name: str) -> requests.Response:
        """Delete a realm role.

        Parameters
        ----------
        role_name : str
            The role name to delete

        Returns
        -------
        requests.Response
            Response from the delete request
        """
        return self._make_admin_request(f"roles/{role_name}", method="DELETE")

    def create_client_role(self, client_id: str, role_data: dict) -> requests.Response:
        """Create a new client role.

        Parameters
        ----------
        client_id : str
            The Keycloak client internal ID
        role_data : dict
            Role data including name and description

        Returns
        -------
        requests.Response
            Response from the create role request
        """
        return self._make_admin_request(
            f"clients/{client_id}/roles", method="POST", json_data=role_data
        )

    def get_client_roles(self, client_id: str) -> requests.Response:
        """Get all roles for a specific client.

        Parameters
        ----------
        client_id : str
            The Keycloak client internal ID

        Returns
        -------
        requests.Response
            Response containing list of client roles
        """
        return self._make_admin_request(f"clients/{client_id}/roles")

    def get_client_role_by_name(
        self, client_id: str, role_name: str
    ) -> requests.Response:
        """Get a specific client role by name.

        Parameters
        ----------
        client_id : str
            The Keycloak client internal ID
        role_name : str
            The role name

        Returns
        -------
        requests.Response
            Response containing role data
        """
        return self._make_admin_request(f"clients/{client_id}/roles/{role_name}")

    def delete_client_role(self, client_id: str, role_name: str) -> requests.Response:
        """Delete a client role.

        Parameters
        ----------
        client_id : str
            The Keycloak client internal ID
        role_name : str
            The role name to delete

        Returns
        -------
        requests.Response
            Response from the delete request
        """
        return self._make_admin_request(
            f"clients/{client_id}/roles/{role_name}", method="DELETE"
        )

    def assign_realm_roles_to_user(
        self, user_id: str, roles: list
    ) -> requests.Response:
        """Assign realm roles to a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        roles : list
            List of role representations (must include 'id' and 'name')

        Returns
        -------
        requests.Response
            Response from the assignment request
        """
        return self._make_admin_request(
            f"users/{user_id}/role-mappings/realm", method="POST", json_data=roles
        )

    def get_user_realm_roles(self, user_id: str) -> requests.Response:
        """Get realm roles assigned to a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID

        Returns
        -------
        requests.Response
            Response containing list of user's realm roles
        """
        return self._make_admin_request(f"users/{user_id}/role-mappings/realm")

    def remove_realm_roles_from_user(
        self, user_id: str, roles: list
    ) -> requests.Response:
        """Remove realm roles from a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        roles : list
            List of role representations to remove

        Returns
        -------
        requests.Response
            Response from the removal request
        """
        return self._make_admin_request(
            f"users/{user_id}/role-mappings/realm", method="DELETE", json_data=roles
        )

    def assign_client_roles_to_user(
        self, user_id: str, client_id: str, roles: list
    ) -> requests.Response:
        """Assign client roles to a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        client_id : str
            The Keycloak client internal ID
        roles : list
            List of role representations

        Returns
        -------
        requests.Response
            Response from the assignment request
        """
        return self._make_admin_request(
            f"users/{user_id}/role-mappings/clients/{client_id}",
            method="POST",
            json_data=roles,
        )

    def get_user_client_roles(self, user_id: str, client_id: str) -> requests.Response:
        """Get client roles assigned to a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        client_id : str
            The Keycloak client internal ID

        Returns
        -------
        requests.Response
            Response containing list of user's client roles
        """
        return self._make_admin_request(
            f"users/{user_id}/role-mappings/clients/{client_id}"
        )

    def remove_client_roles_from_user(
        self, user_id: str, client_id: str, roles: list
    ) -> requests.Response:
        """Remove client roles from a user.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        client_id : str
            The Keycloak client internal ID
        roles : list
            List of role representations to remove

        Returns
        -------
        requests.Response
            Response from the removal request
        """
        return self._make_admin_request(
            f"users/{user_id}/role-mappings/clients/{client_id}",
            method="DELETE",
            json_data=roles,
        )

    def create_group(self, group_data: dict) -> requests.Response:
        """Create a new group.

        Parameters
        ----------
        group_data : dict
            Group data including name
            Example: {"name": "test-group"}

        Returns
        -------
        requests.Response
            Response from the create group request
        """
        return self._make_admin_request("groups", method="POST", json_data=group_data)

    def get_groups(self) -> requests.Response:
        """Get all groups.

        Returns
        -------
        requests.Response
            Response containing list of groups
        """
        return self._make_admin_request("groups")

    def get_group_by_id(self, group_id: str) -> requests.Response:
        """Get a specific group by ID.

        Parameters
        ----------
        group_id : str
            The Keycloak group ID

        Returns
        -------
        requests.Response
            Response containing group data
        """
        return self._make_admin_request(f"groups/{group_id}")

    def delete_group(self, group_id: str) -> requests.Response:
        """Delete a group.

        Parameters
        ----------
        group_id : str
            The Keycloak group ID to delete

        Returns
        -------
        requests.Response
            Response from the delete request
        """
        return self._make_admin_request(f"groups/{group_id}", method="DELETE")

    def add_user_to_group(self, user_id: str, group_id: str) -> requests.Response:
        """Add a user to a group.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        group_id : str
            The Keycloak group ID

        Returns
        -------
        requests.Response
            Response from the add user request
        """
        return self._make_admin_request(
            f"users/{user_id}/groups/{group_id}", method="PUT"
        )

    def remove_user_from_group(self, user_id: str, group_id: str) -> requests.Response:
        """Remove a user from a group.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID
        group_id : str
            The Keycloak group ID

        Returns
        -------
        requests.Response
            Response from the remove user request
        """
        return self._make_admin_request(
            f"users/{user_id}/groups/{group_id}", method="DELETE"
        )

    def get_user_groups(self, user_id: str) -> requests.Response:
        """Get groups that a user is a member of.

        Parameters
        ----------
        user_id : str
            The Keycloak user ID

        Returns
        -------
        requests.Response
            Response containing list of user's groups
        """
        return self._make_admin_request(f"users/{user_id}/groups")

    def get_group_members(self, group_id: str) -> requests.Response:
        """Get members of a group.

        Parameters
        ----------
        group_id : str
            The Keycloak group ID

        Returns
        -------
        requests.Response
            Response containing list of group members
        """
        return self._make_admin_request(f"groups/{group_id}/members")

    def assign_realm_roles_to_group(
        self, group_id: str, roles: list
    ) -> requests.Response:
        """Assign realm roles to a group.

        Parameters
        ----------
        group_id : str
            The Keycloak group ID
        roles : list
            List of role representations

        Returns
        -------
        requests.Response
            Response from the assignment request
        """
        return self._make_admin_request(
            f"groups/{group_id}/role-mappings/realm", method="POST", json_data=roles
        )

    def get_group_realm_roles(self, group_id: str) -> requests.Response:
        """Get realm roles assigned to a group.

        Parameters
        ----------
        group_id : str
            The Keycloak group ID

        Returns
        -------
        requests.Response
            Response containing list of group's realm roles
        """
        return self._make_admin_request(f"groups/{group_id}/role-mappings/realm")

    def create_subgroup(
        self, parent_group_id: str, group_data: dict
    ) -> requests.Response:
        """Create a subgroup under a parent group.

        Parameters
        ----------
        parent_group_id : str
            The Keycloak parent group ID
        group_data : dict
            Group data including name

        Returns
        -------
        requests.Response
            Response from the create subgroup request
        """
        return self._make_admin_request(
            f"groups/{parent_group_id}/children", method="POST", json_data=group_data
        )

    def oauth2_client_credentials_flow(
        self, client_id: str, client_secret: str
    ) -> dict:
        """Perform OAuth2 client credentials flow.

        Parameters
        ----------
        client_id : str
            The OAuth2 client ID
        client_secret : str
            The OAuth2 client secret

        Returns
        -------
        dict
            Token response containing access_token
        """
        token_url = self._get_token_url()

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            token_url,
            data=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=TIMEOUT,
        )

        response.raise_for_status()
        return response.json()

    def oauth2_password_flow(
        self, client_id: str, username: str, password: str, client_secret: str = None
    ) -> dict:
        """Perform OAuth2 resource owner password flow.

        Parameters
        ----------
        client_id : str
            The OAuth2 client ID
        username : str
            Username for authentication
        password : str
            Password for authentication
        client_secret : str, optional
            The OAuth2 client secret (for confidential clients)

        Returns
        -------
        dict
            Token response containing access_token
        """
        token_url = self._get_token_url()

        payload = {
            "grant_type": "password",
            "client_id": client_id,
            "username": username,
            "password": password,
        }

        if client_secret:
            payload["client_secret"] = client_secret

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(
            token_url,
            data=payload,
            headers=headers,
            verify=self.verify_ssl,
            timeout=TIMEOUT,
        )

        response.raise_for_status()
        return response.json()
