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
