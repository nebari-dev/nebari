"""Keycloak API endpoint tests."""

import os

import pytest
import requests


@pytest.fixture(scope="session")
def keycloak_base_url() -> str:
    """Get the base URL for Keycloak."""
    return os.getenv("KEYCLOAK_BASE_URL", "https://tylertesting42.io/auth/")


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


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_keycloak_login_with_credentials(
    keycloak_base_url: str,
    keycloak_username: str,
    keycloak_password: str,
    keycloak_realm: str,
    keycloak_client_id: str,
    verify_ssl: bool,
) -> None:
    """Test that we can authenticate with Keycloak using username/password."""
    # Construct the token endpoint URL
    token_url = f"{keycloak_base_url}realms/{keycloak_realm}/protocol/openid-connect/token"

    # Prepare the authentication request
    payload = {
        "grant_type": "password",
        "client_id": keycloak_client_id,
        "username": keycloak_username,
        "password": keycloak_password,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Make the authentication request
    response = requests.post(
        token_url,
        data=payload,
        headers=headers,
        verify=verify_ssl,
    )

    # Assert successful authentication
    assert response.status_code == 200, f"Authentication failed: {response.text}"

    # Verify the response contains expected fields
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"].lower() == "bearer"
    assert "expires_in" in token_data


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_keycloak_login_invalid_credentials(
    keycloak_base_url: str,
    keycloak_realm: str,
    keycloak_client_id: str,
    verify_ssl: bool,
) -> None:
    """Test that authentication fails with invalid credentials."""
    token_url = f"{keycloak_base_url}realms/{keycloak_realm}/protocol/openid-connect/token"

    payload = {
        "grant_type": "password",
        "client_id": keycloak_client_id,
        "username": "invalid_user",
        "password": "invalid_password",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        token_url,
        data=payload,
        headers=headers,
        verify=verify_ssl,
    )

    # Assert authentication fails
    assert response.status_code == 401
