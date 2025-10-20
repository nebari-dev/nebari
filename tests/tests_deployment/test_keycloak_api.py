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


@pytest.fixture(scope="session")
def authenticated_keycloak_api(
    keycloak_base_url: str,
    keycloak_username: str,
    keycloak_password: str,
    keycloak_realm: str,
    keycloak_client_id: str,
    verify_ssl: bool,
) -> KeycloakAPI:
    """Create an authenticated KeycloakAPI instance for admin operations."""
    api = KeycloakAPI(
        base_url=keycloak_base_url,
        realm=keycloak_realm,
        client_id=keycloak_client_id,
        username=keycloak_username,
        password=keycloak_password,
        verify_ssl=verify_ssl,
    )
    return api


@pytest.fixture
def test_username() -> str:
    """Generate a unique test username."""
    import uuid
    return f"testuser_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_client_id() -> str:
    """Generate a unique test client ID."""
    import uuid
    return f"test-client-{uuid.uuid4().hex[:8]}"


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


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_create_user(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test creating a new user in Keycloak."""
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "firstName": "Test",
        "lastName": "User",
        "enabled": True,
    }

    response = authenticated_keycloak_api.create_user(user_data)

    # Keycloak returns 201 Created for successful user creation
    assert response.status_code == 201, f"Failed to create user: {response.text}"

    # Cleanup: Delete the created user
    # Get the user to retrieve the ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    assert get_response.status_code == 200
    users = get_response.json()
    if users:
        user_id = users[0]["id"]
        authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_users(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test getting users from Keycloak."""
    response = authenticated_keycloak_api.get_users()

    assert response.status_code == 200, f"Failed to get users: {response.text}"
    users = response.json()
    assert isinstance(users, list), "Expected a list of users"


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_user_by_username(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test getting a specific user by username."""
    # First, create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == 201

    # Get the user by username
    response = authenticated_keycloak_api.get_users(username=test_username)
    assert response.status_code == 200, f"Failed to get user: {response.text}"

    users = response.json()
    assert len(users) > 0, "User not found"
    assert users[0]["username"] == test_username

    # Cleanup: Delete the test user
    user_id = users[0]["id"]
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_update_user(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test updating a user in Keycloak."""
    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "firstName": "Original",
        "lastName": "Name",
        "enabled": True,
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == 201

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Update the user
    update_data = {
        "firstName": "Updated",
        "lastName": "User",
    }
    update_response = authenticated_keycloak_api.update_user(user_id, update_data)
    assert update_response.status_code == 204, f"Failed to update user: {update_response.text}"

    # Verify the update
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    assert verify_response.status_code == 200
    updated_user = verify_response.json()
    assert updated_user["firstName"] == "Updated"
    assert updated_user["lastName"] == "User"

    # Cleanup: Delete the test user
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_delete_user(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test deleting a user from Keycloak."""
    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == 201

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Delete the user
    delete_response = authenticated_keycloak_api.delete_user(user_id)
    assert delete_response.status_code == 204, f"Failed to delete user: {delete_response.text}"

    # Verify the user is deleted
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    assert verify_response.status_code == 404, "User should not exist after deletion"


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_create_client(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test creating a new client in Keycloak."""
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "redirectUris": ["http://localhost:8080/*"],
    }

    response = authenticated_keycloak_api.create_client(client_data)

    # Keycloak returns 201 Created for successful client creation
    assert response.status_code == 201, f"Failed to create client: {response.text}"

    # Cleanup: Delete the created client
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    assert get_response.status_code == 200
    clients = get_response.json()
    if clients:
        client_internal_id = clients[0]["id"]
        authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_clients(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test getting clients from Keycloak."""
    response = authenticated_keycloak_api.get_clients()

    assert response.status_code == 200, f"Failed to get clients: {response.text}"
    clients = response.json()
    assert isinstance(clients, list), "Expected a list of clients"


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_client_by_client_id(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test getting a specific client by clientId."""
    # First, create a test client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": True,
        "protocol": "openid-connect",
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == 201

    # Get the client by clientId
    response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    assert response.status_code == 200, f"Failed to get client: {response.text}"

    clients = response.json()
    assert len(clients) > 0, "Client not found"
    assert clients[0]["clientId"] == test_client_id

    # Cleanup: Delete the test client
    client_internal_id = clients[0]["id"]
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_update_client(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test updating a client in Keycloak."""
    # Create a test client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": True,
        "protocol": "openid-connect",
        "description": "Original description",
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == 201

    # Get the client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    # Update the client
    update_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "description": "Updated description",
    }
    update_response = authenticated_keycloak_api.update_client(client_internal_id, update_data)
    assert update_response.status_code == 204, f"Failed to update client: {update_response.text}"

    # Verify the update
    verify_response = authenticated_keycloak_api.get_client_by_id(client_internal_id)
    assert verify_response.status_code == 200
    updated_client = verify_response.json()
    assert updated_client["description"] == "Updated description"
    assert updated_client["publicClient"] is False

    # Cleanup: Delete the test client
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_delete_client(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test deleting a client from Keycloak."""
    # Create a test client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": True,
        "protocol": "openid-connect",
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == 201

    # Get the client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    # Delete the client
    delete_response = authenticated_keycloak_api.delete_client(client_internal_id)
    assert delete_response.status_code == 204, f"Failed to delete client: {delete_response.text}"

    # Verify the client is deleted
    verify_response = authenticated_keycloak_api.get_client_by_id(client_internal_id)
    assert verify_response.status_code == 404, "Client should not exist after deletion"
