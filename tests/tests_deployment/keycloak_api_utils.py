"""Helper class for Keycloak API interactions."""

import requests

TIMEOUT = 10


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
        self.base_url = base_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_type = None

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
