"""Keycloak API endpoint tests."""

import os

import pytest
import requests
from .keycloak_api_utils import KeycloakAPI


@pytest.fixture(scope="session")
def keycloak_base_url() -> str:
    """Get the base URL for Keycloak."""
    return os.getenv("KEYCLOAK_BASE_URL", "https://tylertesting42.io/auth")


@pytest.fixture(scope="session")
def keycloak_username() -> str:
    """Get the Keycloak admin username."""
    return os.getenv("KEYCLOAK_USERNAME", "root")


@pytest.fixture(scope="session")
def keycloak_password() -> str:
    """Get the Keycloak admin password."""
    return os.getenv("KEYCLOAK_PASSWORD", "e7kjiszh9ykuzhkopnnw7vmgixyl5vto")


@pytest.fixture(scope="session")
def keycloak_realm() -> str:
    """Get the Keycloak realm name."""
    return os.getenv("KEYCLOAK_REALM", "master")


@pytest.fixture(scope="session")
def keycloak_client_id() -> str:
    """Get the Keycloak client ID for authentication."""
    return os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")


@pytest.fixture(scope="session")
def verify_ssl() -> bool:
    """Determine if SSL verification should be enabled.

    If KEYCLOAK_VERIFY_SSL is 1 or true, SSL verification is enabled.
    For all other inputs, SSL verification is disabled (default).
    """
    verify = os.environ.get("KEYCLOAK_VERIFY_SSL", "false")
    return verify.lower() in ("1", "true")


@pytest.fixture(scope="session")
def keycloak_api(
    keycloak_base_url: str,
    keycloak_realm: str,
    keycloak_client_id: str,
    verify_ssl: bool,
) -> KeycloakAPI:
    """Create a KeycloakAPI instance without authentication."""
    return KeycloakAPI(
        base_url=keycloak_base_url,
        realm=keycloak_realm,
        client_id=keycloak_client_id,
        verify_ssl=verify_ssl,
    )


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_keycloak_login_with_credentials(
    keycloak_api: KeycloakAPI,
    keycloak_username: str,
    keycloak_password: str,
) -> None:
    """Test that we can authenticate with Keycloak using username/password."""
    # Authenticate using KeycloakAPI
    token_data = keycloak_api.authenticate(keycloak_username, keycloak_password)

    # Verify the response contains expected fields
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"].lower() == "bearer"
    assert "expires_in" in token_data

    # Verify tokens are stored in the instance
    assert keycloak_api.access_token is not None
    assert keycloak_api.refresh_token is not None
    assert keycloak_api.token_type == "Bearer"


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_keycloak_login_invalid_credentials(
    keycloak_api: KeycloakAPI,
) -> None:
    """Test that authentication fails with invalid credentials."""
    # Authenticate with invalid credentials should raise an HTTPError
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        keycloak_api.authenticate("invalid_user", "invalid_password")

    # Verify it's a 401 Unauthorized error
    assert exc_info.value.response.status_code == 401
