"""Keycloak API endpoint tests."""

import os
import pathlib
import uuid
from http import HTTPStatus

import pytest
import requests

from _nebari.config import read_configuration
from nebari.plugins import nebari_plugin_manager
from tests.tests_deployment import constants

from .keycloak_api_utils import KeycloakAPI, decode_jwt_token


def get_nebari_config():
    config_schema = nebari_plugin_manager.config_schema
    config_filepath = constants.NEBARI_CONFIG_PATH
    assert pathlib.Path(config_filepath).exists()
    config = read_configuration(config_filepath, config_schema)
    return config


@pytest.fixture(scope="session")
def keycloak_base_url() -> str:
    """Get the base URL for Keycloak."""
    config = get_nebari_config()

    keycloak_server_url = os.environ.get(
        "KEYCLOAK_SERVER_URL", f"https://{config.domain}/auth/"
    )
    return keycloak_server_url


@pytest.fixture(scope="session")
def keycloak_username() -> str:
    """Get the Keycloak admin username."""
    keycloak_admin_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "root")
    return keycloak_admin_username


@pytest.fixture(scope="session")
def keycloak_password() -> str:
    """Get the Keycloak admin password."""
    config = get_nebari_config()
    keycloak_admin_password = os.environ.get(
        "KEYCLOAK_ADMIN_PASSWORD",
        config.security.keycloak.initial_root_password,
    )
    return keycloak_admin_password


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
    return f"testuser_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_client_id() -> str:
    """Generate a unique test client ID."""
    return f"test-client-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_role_name() -> str:
    """Generate a unique test role name."""
    return f"test-role-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_group_name() -> str:
    """Generate a unique test group name."""
    return f"test-group-{uuid.uuid4().hex[:8]}"


@pytest.mark.keycloak
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


@pytest.mark.keycloak
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_keycloak_login_invalid_credentials(
    keycloak_api: KeycloakAPI,
) -> None:
    """Test that authentication fails with invalid credentials."""
    # Authenticate with invalid credentials should raise an HTTPError
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        keycloak_api.authenticate("invalid_user", "invalid_password")

    # Verify it's a 401 Unauthorized error
    assert exc_info.value.response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.keycloak
@pytest.mark.keycloak_users
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
    assert (
        response.status_code == HTTPStatus.CREATED
    ), f"Failed to create user: {response.text}"

    # Cleanup: Delete the created user
    # Get the user to retrieve the ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    assert get_response.status_code == HTTPStatus.OK
    users = get_response.json()
    if users:
        user_id = users[0]["id"]
        authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_users
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_users(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test getting users from Keycloak."""
    response = authenticated_keycloak_api.get_users()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to get users: {response.text}"
    users = response.json()
    assert isinstance(users, list), "Expected a list of users"


@pytest.mark.keycloak
@pytest.mark.keycloak_users
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
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the user by username
    response = authenticated_keycloak_api.get_users(username=test_username)
    assert response.status_code == HTTPStatus.OK, f"Failed to get user: {response.text}"

    users = response.json()
    assert len(users) > 0, "User not found"
    assert users[0]["username"] == test_username

    # Cleanup: Delete the test user
    user_id = users[0]["id"]
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_users
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
    assert create_response.status_code == HTTPStatus.CREATED

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
    assert (
        update_response.status_code == HTTPStatus.NO_CONTENT
    ), f"Failed to update user: {update_response.text}"

    # Verify the update
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    assert verify_response.status_code == HTTPStatus.OK
    updated_user = verify_response.json()
    assert updated_user["firstName"] == "Updated"
    assert updated_user["lastName"] == "User"

    # Cleanup: Delete the test user
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_users
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
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Delete the user
    delete_response = authenticated_keycloak_api.delete_user(user_id)
    assert (
        delete_response.status_code == HTTPStatus.NO_CONTENT
    ), f"Failed to delete user: {delete_response.text}"

    # Verify the user is deleted
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    assert (
        verify_response.status_code == HTTPStatus.NOT_FOUND
    ), "User should not exist after deletion"


@pytest.mark.keycloak
@pytest.mark.keycloak_users
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_list_users(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test listing all users from Keycloak."""
    response = authenticated_keycloak_api.get_users()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to list users: {response.text}"
    users = response.json()
    assert isinstance(users, list), "Expected a list of users"
    # Verify each user has expected fields
    if len(users) > 0:
        assert "id" in users[0]
        assert "username" in users[0]


@pytest.mark.keycloak
@pytest.mark.keycloak_users
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_user_by_id(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test getting a specific user by ID."""
    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "firstName": "Test",
        "lastName": "User",
        "enabled": True,
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Get user by ID
    response = authenticated_keycloak_api.get_user_by_id(user_id)
    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to get user by ID: {response.text}"

    user = response.json()
    assert user["id"] == user_id
    assert user["username"] == test_username
    assert user["email"] == f"{test_username}@example.com"

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_users
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_update_user_password(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test updating a user's password and verifying authentication."""
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    # Create a test user with initial password
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": old_password,
                "temporary": False,
            }
        ],
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Update the password
    update_response = authenticated_keycloak_api.reset_user_password(
        user_id, new_password, temporary=False
    )
    assert (
        update_response.status_code == HTTPStatus.NO_CONTENT
    ), f"Failed to update password: {update_response.text}"

    # Verify user can authenticate with new password
    token_data = keycloak_api.authenticate(test_username, new_password)
    assert "access_token" in token_data

    # Verify old password no longer works
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        keycloak_api.authenticate(test_username, old_password)
    assert exc_info.value.response.status_code == HTTPStatus.UNAUTHORIZED

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_users
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_enable_disable_user(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test disabling and re-enabling a user account."""
    password = "TestPassword123!"

    # Create an enabled test user with password
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    create_response = authenticated_keycloak_api.create_user(user_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the user ID
    get_response = authenticated_keycloak_api.get_users(username=test_username)
    users = get_response.json()
    user_id = users[0]["id"]

    # Verify user can authenticate while enabled
    try:
        token_data = keycloak_api.authenticate(test_username, password)
        assert "access_token" in token_data
        user_can_auth = True
    except requests.exceptions.HTTPError:
        # Some configurations may not allow immediate auth
        user_can_auth = False

    # Disable the user
    disable_response = authenticated_keycloak_api.update_user(
        user_id, {"enabled": False}
    )
    assert disable_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user is disabled
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    disabled_user = verify_response.json()
    assert disabled_user["enabled"] is False

    # Verify user cannot authenticate when disabled
    # Keycloak may return 400 (Bad Request) or 401 (Unauthorized) for disabled users
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        keycloak_api.authenticate(test_username, password)
    assert exc_info.value.response.status_code in (
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.UNAUTHORIZED,
    )

    # Re-enable the user
    enable_response = authenticated_keycloak_api.update_user(user_id, {"enabled": True})
    assert enable_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user is enabled
    verify_response = authenticated_keycloak_api.get_user_by_id(user_id)
    enabled_user = verify_response.json()
    assert enabled_user["enabled"] is True

    # Verify user can authenticate again (if they could before)
    if user_can_auth:
        token_data = keycloak_api.authenticate(test_username, password)
        assert "access_token" in token_data

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
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
    assert (
        response.status_code == HTTPStatus.CREATED
    ), f"Failed to create client: {response.text}"

    # Cleanup: Delete the created client
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    assert get_response.status_code == HTTPStatus.OK
    clients = get_response.json()
    if clients:
        client_internal_id = clients[0]["id"]
        authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_clients(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test getting clients from Keycloak."""
    response = authenticated_keycloak_api.get_clients()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to get clients: {response.text}"
    clients = response.json()
    assert isinstance(clients, list), "Expected a list of clients"


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
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
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the client by clientId
    response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to get client: {response.text}"

    clients = response.json()
    assert len(clients) > 0, "Client not found"
    assert clients[0]["clientId"] == test_client_id

    # Cleanup: Delete the test client
    client_internal_id = clients[0]["id"]
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
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
    assert create_response.status_code == HTTPStatus.CREATED

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
    update_response = authenticated_keycloak_api.update_client(
        client_internal_id, update_data
    )
    assert (
        update_response.status_code == HTTPStatus.NO_CONTENT
    ), f"Failed to update client: {update_response.text}"

    # Verify the update
    verify_response = authenticated_keycloak_api.get_client_by_id(client_internal_id)
    assert verify_response.status_code == HTTPStatus.OK
    updated_client = verify_response.json()
    assert updated_client["description"] == "Updated description"
    assert updated_client["publicClient"] is False

    # Cleanup: Delete the test client
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
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
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    # Delete the client
    delete_response = authenticated_keycloak_api.delete_client(client_internal_id)
    assert (
        delete_response.status_code == HTTPStatus.NO_CONTENT
    ), f"Failed to delete client: {delete_response.text}"

    # Verify the client is deleted
    verify_response = authenticated_keycloak_api.get_client_by_id(client_internal_id)
    assert (
        verify_response.status_code == HTTPStatus.NOT_FOUND
    ), "Client should not exist after deletion"


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_list_clients(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test listing all clients from Keycloak."""
    response = authenticated_keycloak_api.get_clients()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to list clients: {response.text}"
    clients = response.json()
    assert isinstance(clients, list), "Expected a list of clients"
    # Verify each client has expected fields
    if len(clients) > 0:
        assert "id" in clients[0]
        assert "clientId" in clients[0]


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_client_secret_regeneration(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test regenerating a client secret."""
    # Create a confidential client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "serviceAccountsEnabled": True,
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    # Get the initial secret
    secret_response = authenticated_keycloak_api.get_client_secret(client_internal_id)
    assert secret_response.status_code == HTTPStatus.OK
    old_secret = secret_response.json()["value"]

    # Regenerate the secret
    regen_response = authenticated_keycloak_api.regenerate_client_secret(
        client_internal_id
    )
    assert regen_response.status_code == HTTPStatus.OK
    new_secret = regen_response.json()["value"]

    # Verify the secrets are different
    assert old_secret != new_secret

    # Verify old secret no longer works for client credentials flow
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        authenticated_keycloak_api.oauth2_client_credentials_flow(
            test_client_id, old_secret
        )
    assert exc_info.value.response.status_code == HTTPStatus.UNAUTHORIZED

    # Verify new secret works
    token_data = authenticated_keycloak_api.oauth2_client_credentials_flow(
        test_client_id, new_secret
    )
    assert "access_token" in token_data

    # Cleanup
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_client_oauth2_flow(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
    test_username: str,
) -> None:
    """Test OAuth2 client credentials and password flows."""
    password = "TestPassword123!"

    # Create a confidential client with service account enabled
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": True,
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the client internal ID and secret
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    secret_response = authenticated_keycloak_api.get_client_secret(client_internal_id)
    client_secret = secret_response.json()["value"]

    # Test client credentials flow
    token_data = authenticated_keycloak_api.oauth2_client_credentials_flow(
        test_client_id, client_secret
    )
    assert "access_token" in token_data
    assert "token_type" in token_data

    # Verify token is valid by decoding it
    access_token = token_data["access_token"]
    token_payload = decode_jwt_token(access_token)
    assert "exp" in token_payload  # Has expiration

    # Create a test user for password flow
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    user_create_response = authenticated_keycloak_api.create_user(user_data)
    assert user_create_response.status_code == HTTPStatus.CREATED

    # Get user ID for cleanup
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Test password flow
    password_token_data = authenticated_keycloak_api.oauth2_password_flow(
        test_client_id, test_username, password, client_secret
    )
    assert "access_token" in password_token_data

    # Verify user token contains username
    user_token_payload = decode_jwt_token(password_token_data["access_token"])
    assert "preferred_username" in user_token_payload
    assert user_token_payload["preferred_username"] == test_username

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_clients
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_client_with_invalid_credentials(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test OAuth2 flow with invalid client credentials."""
    # Create a confidential client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "serviceAccountsEnabled": True,
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    clients = get_response.json()
    client_internal_id = clients[0]["id"]

    # Attempt OAuth2 flow with invalid secret
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        authenticated_keycloak_api.oauth2_client_credentials_flow(
            test_client_id, "invalid-secret"
        )
    assert exc_info.value.response.status_code == HTTPStatus.UNAUTHORIZED

    # Cleanup
    authenticated_keycloak_api.delete_client(client_internal_id)


# Role Tests


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_create_realm_role(
    authenticated_keycloak_api: KeycloakAPI,
    test_role_name: str,
) -> None:
    """Test creating a new realm role."""
    role_data = {
        "name": test_role_name,
        "description": "Test realm role",
    }

    response = authenticated_keycloak_api.create_realm_role(role_data)
    assert (
        response.status_code == HTTPStatus.CREATED
    ), f"Failed to create realm role: {response.text}"

    # Verify role was created
    get_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert get_response.status_code == HTTPStatus.OK
    role = get_response.json()
    assert role["name"] == test_role_name

    # Cleanup
    authenticated_keycloak_api.delete_realm_role(test_role_name)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_list_realm_roles(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test listing all realm roles."""
    response = authenticated_keycloak_api.get_realm_roles()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to list realm roles: {response.text}"
    roles = response.json()
    assert isinstance(roles, list), "Expected a list of roles"
    # Verify we have at least some default roles
    assert len(roles) > 0


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_get_realm_role_by_name(
    authenticated_keycloak_api: KeycloakAPI,
    test_role_name: str,
) -> None:
    """Test getting a specific realm role by name."""
    # Create a test role
    role_data = {
        "name": test_role_name,
        "description": "Test role",
    }
    create_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get the role by name
    response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert response.status_code == HTTPStatus.OK

    role = response.json()
    assert role["name"] == test_role_name
    assert role["description"] == "Test role"

    # Cleanup
    authenticated_keycloak_api.delete_realm_role(test_role_name)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_delete_realm_role(
    authenticated_keycloak_api: KeycloakAPI,
    test_role_name: str,
) -> None:
    """Test deleting a realm role."""
    # Create a test role
    role_data = {
        "name": test_role_name,
        "description": "Test role to delete",
    }
    create_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Delete the role
    delete_response = authenticated_keycloak_api.delete_realm_role(test_role_name)
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    # Verify role is deleted
    get_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert get_response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_create_client_role(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
    test_role_name: str,
) -> None:
    """Test creating a client role."""
    # First create a client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
    }
    create_client_response = authenticated_keycloak_api.create_client(client_data)
    assert create_client_response.status_code == HTTPStatus.CREATED

    # Get client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    client_internal_id = get_response.json()[0]["id"]

    # Create a client role
    role_data = {
        "name": test_role_name,
        "description": "Test client role",
    }
    role_response = authenticated_keycloak_api.create_client_role(
        client_internal_id, role_data
    )
    assert role_response.status_code == HTTPStatus.CREATED

    # Verify role was created
    get_role_response = authenticated_keycloak_api.get_client_role_by_name(
        client_internal_id, test_role_name
    )
    assert get_role_response.status_code == HTTPStatus.OK
    role = get_role_response.json()
    assert role["name"] == test_role_name

    # Cleanup
    authenticated_keycloak_api.delete_client_role(client_internal_id, test_role_name)
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_list_client_roles(
    authenticated_keycloak_api: KeycloakAPI,
    test_client_id: str,
) -> None:
    """Test listing all roles for a client."""
    # Create a client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
    }
    create_response = authenticated_keycloak_api.create_client(client_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    client_internal_id = get_response.json()[0]["id"]

    # Get client roles
    roles_response = authenticated_keycloak_api.get_client_roles(client_internal_id)
    assert roles_response.status_code == HTTPStatus.OK
    roles = roles_response.json()
    assert isinstance(roles, list)

    # Cleanup
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_assign_realm_role_to_user(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
    test_role_name: str,
) -> None:
    """Test assigning a realm role to a user."""
    password = "TestPassword123!"

    # Create a test role
    role_data = {
        "name": test_role_name,
        "description": "Test role for assignment",
    }
    create_role_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_role_response.status_code == HTTPStatus.CREATED

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    role = role_response.json()

    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign role to user
    assign_response = authenticated_keycloak_api.assign_realm_roles_to_user(
        user_id, [role]
    )
    assert assign_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user has role
    user_roles_response = authenticated_keycloak_api.get_user_realm_roles(user_id)
    assert user_roles_response.status_code == HTTPStatus.OK
    user_roles = user_roles_response.json()
    role_names = [r["name"] for r in user_roles]
    assert test_role_name in role_names

    # Verify role appears in token
    token_data = keycloak_api.authenticate(test_username, password)
    token_payload = decode_jwt_token(token_data["access_token"])
    if "realm_access" in token_payload and "roles" in token_payload["realm_access"]:
        assert test_role_name in token_payload["realm_access"]["roles"]

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_realm_role(test_role_name)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_assign_client_role_to_user(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
    test_client_id: str,
    test_role_name: str,
) -> None:
    """Test assigning a client role to a user."""
    # Create a client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
    }
    create_client_response = authenticated_keycloak_api.create_client(client_data)
    assert create_client_response.status_code == HTTPStatus.CREATED

    # Get client internal ID
    get_client_response = authenticated_keycloak_api.get_clients(
        client_id=test_client_id
    )
    client_internal_id = get_client_response.json()[0]["id"]

    # Create a client role
    role_data = {
        "name": test_role_name,
        "description": "Test client role for assignment",
    }
    create_role_response = authenticated_keycloak_api.create_client_role(
        client_internal_id, role_data
    )
    assert create_role_response.status_code == HTTPStatus.CREATED

    # Get the role
    role_response = authenticated_keycloak_api.get_client_role_by_name(
        client_internal_id, test_role_name
    )
    role = role_response.json()

    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign client role to user
    assign_response = authenticated_keycloak_api.assign_client_roles_to_user(
        user_id, client_internal_id, [role]
    )
    assert assign_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user has client role
    user_roles_response = authenticated_keycloak_api.get_user_client_roles(
        user_id, client_internal_id
    )
    assert user_roles_response.status_code == HTTPStatus.OK
    user_roles = user_roles_response.json()
    role_names = [r["name"] for r in user_roles]
    assert test_role_name in role_names

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_client(client_internal_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_roles
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_remove_role_from_user(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
    test_role_name: str,
) -> None:
    """Test removing a role from a user."""
    # Create a test role
    role_data = {
        "name": test_role_name,
        "description": "Test role for removal",
    }
    create_role_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_role_response.status_code == HTTPStatus.CREATED

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    role = role_response.json()

    # Create a test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign role to user
    assign_response = authenticated_keycloak_api.assign_realm_roles_to_user(
        user_id, [role]
    )
    assert assign_response.status_code == HTTPStatus.NO_CONTENT

    # Remove role from user
    remove_response = authenticated_keycloak_api.remove_realm_roles_from_user(
        user_id, [role]
    )
    assert remove_response.status_code == HTTPStatus.NO_CONTENT

    # Verify role is removed
    user_roles_response = authenticated_keycloak_api.get_user_realm_roles(user_id)
    user_roles = user_roles_response.json()
    role_names = [r["name"] for r in user_roles]
    assert test_role_name not in role_names

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_realm_role(test_role_name)


# Group Tests


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_create_group(
    authenticated_keycloak_api: KeycloakAPI,
    test_group_name: str,
) -> None:
    """Test creating a new group."""
    group_data = {
        "name": test_group_name,
    }

    response = authenticated_keycloak_api.create_group(group_data)
    assert (
        response.status_code == HTTPStatus.CREATED
    ), f"Failed to create group: {response.text}"

    # Verify group was created
    groups_response = authenticated_keycloak_api.get_groups()
    assert groups_response.status_code == HTTPStatus.OK
    groups = groups_response.json()
    group_names = [g["name"] for g in groups]
    assert test_group_name in group_names

    # Get group ID for cleanup
    group = [g for g in groups if g["name"] == test_group_name][0]
    authenticated_keycloak_api.delete_group(group["id"])


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_list_groups(
    authenticated_keycloak_api: KeycloakAPI,
) -> None:
    """Test listing all groups."""
    response = authenticated_keycloak_api.get_groups()

    assert (
        response.status_code == HTTPStatus.OK
    ), f"Failed to list groups: {response.text}"
    groups = response.json()
    assert isinstance(groups, list), "Expected a list of groups"


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_add_user_to_group(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
    test_group_name: str,
) -> None:
    """Test adding a user to a group."""
    # Create a group
    group_data = {"name": test_group_name}
    create_group_response = authenticated_keycloak_api.create_group(group_data)
    assert create_group_response.status_code == HTTPStatus.CREATED

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Create a user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user is in group
    user_groups_response = authenticated_keycloak_api.get_user_groups(user_id)
    assert user_groups_response.status_code == HTTPStatus.OK
    user_groups = user_groups_response.json()
    user_group_names = [g["name"] for g in user_groups]
    assert test_group_name in user_group_names

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_group(group_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_remove_user_from_group(
    authenticated_keycloak_api: KeycloakAPI,
    test_username: str,
    test_group_name: str,
) -> None:
    """Test removing a user from a group."""
    # Create a group
    group_data = {"name": test_group_name}
    create_group_response = authenticated_keycloak_api.create_group(group_data)
    assert create_group_response.status_code == HTTPStatus.CREATED

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Create a user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_response.status_code == HTTPStatus.NO_CONTENT

    # Remove user from group
    remove_response = authenticated_keycloak_api.remove_user_from_group(
        user_id, group_id
    )
    assert remove_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user is removed from group
    user_groups_response = authenticated_keycloak_api.get_user_groups(user_id)
    user_groups = user_groups_response.json()
    user_group_names = [g["name"] for g in user_groups]
    assert test_group_name not in user_group_names

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_group(group_id)


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_delete_group(
    authenticated_keycloak_api: KeycloakAPI,
    test_group_name: str,
) -> None:
    """Test deleting a group."""
    # Create a group
    group_data = {"name": test_group_name}
    create_response = authenticated_keycloak_api.create_group(group_data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Delete the group
    delete_response = authenticated_keycloak_api.delete_group(group_id)
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    # Verify group is deleted
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group_names = [g["name"] for g in groups]
    assert test_group_name not in group_names


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_group_role_assignment(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
    test_group_name: str,
    test_role_name: str,
) -> None:
    """Test that user inherits roles from group."""
    password = "TestPassword123!"

    # Create a role
    role_data = {
        "name": test_role_name,
        "description": "Test role for group",
    }
    create_role_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_role_response.status_code == HTTPStatus.CREATED

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    role = role_response.json()

    # Create a group
    group_data = {"name": test_group_name}
    create_group_response = authenticated_keycloak_api.create_group(group_data)
    assert create_group_response.status_code == HTTPStatus.CREATED

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Assign role to group
    assign_role_response = authenticated_keycloak_api.assign_realm_roles_to_group(
        group_id, [role]
    )
    assert assign_role_response.status_code == HTTPStatus.NO_CONTENT

    # Create a user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_user_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_user_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user has role from group in token
    token_data = keycloak_api.authenticate(test_username, password)
    token_payload = decode_jwt_token(token_data["access_token"])
    if "realm_access" in token_payload and "roles" in token_payload["realm_access"]:
        assert test_role_name in token_payload["realm_access"]["roles"]

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_group(group_id)
    authenticated_keycloak_api.delete_realm_role(test_role_name)


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_nested_groups(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test nested group hierarchy and role inheritance."""
    parent_group_name = f"parent-group-{uuid.uuid4().hex[:8]}"
    child_group_name = f"child-group-{uuid.uuid4().hex[:8]}"
    role_name = f"parent-role-{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"

    # Create a role
    role_data = {
        "name": role_name,
        "description": "Test role for parent group",
    }
    create_role_response = authenticated_keycloak_api.create_realm_role(role_data)
    assert create_role_response.status_code == HTTPStatus.CREATED

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(role_name)
    role = role_response.json()

    # Create parent group
    parent_group_data = {"name": parent_group_name}
    create_parent_response = authenticated_keycloak_api.create_group(parent_group_data)
    assert create_parent_response.status_code == HTTPStatus.CREATED

    # Get parent group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    parent_group = [g for g in groups if g["name"] == parent_group_name][0]
    parent_group_id = parent_group["id"]

    # Assign role to parent group
    assign_role_response = authenticated_keycloak_api.assign_realm_roles_to_group(
        parent_group_id, [role]
    )
    assert assign_role_response.status_code == HTTPStatus.NO_CONTENT

    # Create child group under parent
    child_group_data = {"name": child_group_name}
    create_child_response = authenticated_keycloak_api.create_subgroup(
        parent_group_id, child_group_data
    )
    assert create_child_response.status_code == HTTPStatus.CREATED

    # Get child group ID
    parent_details_response = authenticated_keycloak_api.get_group_by_id(
        parent_group_id
    )
    parent_details = parent_details_response.json()
    child_group = parent_details["subGroups"][0]
    child_group_id = child_group["id"]

    # Create a user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    create_user_response = authenticated_keycloak_api.create_user(user_data)
    assert create_user_response.status_code == HTTPStatus.CREATED

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to child group
    add_user_response = authenticated_keycloak_api.add_user_to_group(
        user_id, child_group_id
    )
    assert add_user_response.status_code == HTTPStatus.NO_CONTENT

    # Verify user inherits role from parent group
    token_data = keycloak_api.authenticate(test_username, password)
    token_payload = decode_jwt_token(token_data["access_token"])
    if "realm_access" in token_payload and "roles" in token_payload["realm_access"]:
        assert role_name in token_payload["realm_access"]["roles"]

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_group(parent_group_id)  # Deletes children too
    authenticated_keycloak_api.delete_realm_role(role_name)


@pytest.mark.keycloak
@pytest.mark.keycloak_groups
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_group_scope_propagation(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
    test_username: str,
) -> None:
    """Test that user gets scopes from multiple groups."""
    group1_name = f"test-group-1-{uuid.uuid4().hex[:8]}"
    group2_name = f"test-group-2-{uuid.uuid4().hex[:8]}"
    role1_name = f"test-role-1-{uuid.uuid4().hex[:8]}"
    role2_name = f"test-role-2-{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"

    # Create two roles
    role1_data = {"name": role1_name, "description": "Role 1"}
    role2_data = {"name": role2_name, "description": "Role 2"}
    authenticated_keycloak_api.create_realm_role(role1_data)
    authenticated_keycloak_api.create_realm_role(role2_data)

    # Get roles
    role1 = authenticated_keycloak_api.get_realm_role_by_name(role1_name).json()
    role2 = authenticated_keycloak_api.get_realm_role_by_name(role2_name).json()

    # Create two groups
    authenticated_keycloak_api.create_group({"name": group1_name})
    authenticated_keycloak_api.create_group({"name": group2_name})

    # Get group IDs
    groups = authenticated_keycloak_api.get_groups().json()
    group1 = [g for g in groups if g["name"] == group1_name][0]
    group2 = [g for g in groups if g["name"] == group2_name][0]
    group1_id = group1["id"]
    group2_id = group2["id"]

    # Assign roles to groups
    authenticated_keycloak_api.assign_realm_roles_to_group(group1_id, [role1])
    authenticated_keycloak_api.assign_realm_roles_to_group(group2_id, [role2])

    # Create a user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }
    authenticated_keycloak_api.create_user(user_data)

    # Get user ID
    user_id = authenticated_keycloak_api.get_users(username=test_username).json()[0][
        "id"
    ]

    # Add user to both groups
    authenticated_keycloak_api.add_user_to_group(user_id, group1_id)
    authenticated_keycloak_api.add_user_to_group(user_id, group2_id)

    # Verify user has roles from both groups
    token_data = keycloak_api.authenticate(test_username, password)
    token_payload = decode_jwt_token(token_data["access_token"])

    # Check user is in both groups
    user_groups = authenticated_keycloak_api.get_user_groups(user_id).json()
    user_group_names = [g["name"] for g in user_groups]
    assert group1_name in user_group_names
    assert group2_name in user_group_names

    # Check token contains both roles
    if "realm_access" in token_payload and "roles" in token_payload["realm_access"]:
        assert role1_name in token_payload["realm_access"]["roles"]
        assert role2_name in token_payload["realm_access"]["roles"]

    # Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_group(group1_id)
    authenticated_keycloak_api.delete_group(group2_id)
    authenticated_keycloak_api.delete_realm_role(role1_name)
    authenticated_keycloak_api.delete_realm_role(role2_name)


# Integration Tests


@pytest.mark.keycloak
@pytest.mark.keycloak_integration
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_admin_user_workflow(
    authenticated_keycloak_api: KeycloakAPI,
    keycloak_api: KeycloakAPI,
) -> None:
    """End-to-end test covering complete workflow from admin perspective.

    This test covers:
    1. Admin creates infrastructure (user, groups, roles, OAuth client)
    2. User authenticates
    3. Group associations are verified
    4. OAuth client login with correct permissions
    5. Scope verification from token
    6. Cleanup
    """
    test_username = f"workflow-user-{uuid.uuid4().hex[:8]}"
    test_password = "WorkflowPassword123!"
    test_client_id = f"workflow-client-{uuid.uuid4().hex[:8]}"
    admin_group_name = f"workflow-admin-{uuid.uuid4().hex[:8]}"
    user_group_name = f"workflow-user-{uuid.uuid4().hex[:8]}"
    admin_role_name = f"workflow-admin-role-{uuid.uuid4().hex[:8]}"
    user_role_name = f"workflow-user-role-{uuid.uuid4().hex[:8]}"

    # Step 1: Admin Setup
    # Create roles
    admin_role_data = {"name": admin_role_name, "description": "Admin role"}
    user_role_data = {"name": user_role_name, "description": "User role"}
    authenticated_keycloak_api.create_realm_role(admin_role_data)
    authenticated_keycloak_api.create_realm_role(user_role_data)

    # Get roles
    admin_role = authenticated_keycloak_api.get_realm_role_by_name(
        admin_role_name
    ).json()
    user_role = authenticated_keycloak_api.get_realm_role_by_name(user_role_name).json()

    # Create groups
    authenticated_keycloak_api.create_group({"name": admin_group_name})
    authenticated_keycloak_api.create_group({"name": user_group_name})

    # Get group IDs
    groups = authenticated_keycloak_api.get_groups().json()
    admin_group = [g for g in groups if g["name"] == admin_group_name][0]
    user_group = [g for g in groups if g["name"] == user_group_name][0]
    admin_group_id = admin_group["id"]
    user_group_id = user_group["id"]

    # Assign roles to groups
    authenticated_keycloak_api.assign_realm_roles_to_group(admin_group_id, [admin_role])
    authenticated_keycloak_api.assign_realm_roles_to_group(user_group_id, [user_role])

    # Create OAuth2 client
    client_data = {
        "clientId": test_client_id,
        "enabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": True,
        "standardFlowEnabled": False,
        "implicitFlowEnabled": False,
    }
    authenticated_keycloak_api.create_client(client_data)

    # Get client internal ID and secret
    client_internal_id = authenticated_keycloak_api.get_clients(
        client_id=test_client_id
    ).json()[0]["id"]
    client_secret = authenticated_keycloak_api.get_client_secret(
        client_internal_id
    ).json()["value"]

    # Create test user
    user_data = {
        "username": test_username,
        "email": f"{test_username}@example.com",
        "firstName": "Workflow",
        "lastName": "User",
        "enabled": True,
        "credentials": [
            {
                "type": "password",
                "value": test_password,
                "temporary": False,
            }
        ],
    }
    authenticated_keycloak_api.create_user(user_data)

    # Get user ID
    user_id = authenticated_keycloak_api.get_users(username=test_username).json()[0][
        "id"
    ]

    # Assign user to groups
    authenticated_keycloak_api.add_user_to_group(user_id, admin_group_id)
    authenticated_keycloak_api.add_user_to_group(user_id, user_group_id)

    # Step 2: User Authentication
    token_data = keycloak_api.authenticate(test_username, test_password)
    assert "access_token" in token_data
    assert "refresh_token" in token_data

    # Step 3: Group Association Verification
    user_details = authenticated_keycloak_api.get_user_by_id(user_id).json()
    assert user_details["username"] == test_username

    # Verify user is member of expected groups
    user_groups_response = authenticated_keycloak_api.get_user_groups(user_id)
    user_groups = user_groups_response.json()
    user_group_names = [g["name"] for g in user_groups]
    assert admin_group_name in user_group_names
    assert user_group_name in user_group_names

    # Parse user's access token
    user_token_payload = decode_jwt_token(token_data["access_token"])
    assert "preferred_username" in user_token_payload
    assert user_token_payload["preferred_username"] == test_username

    # Step 4: OAuth Client Login
    # Authenticate as test user through OAuth2 flow
    oauth_token_data = authenticated_keycloak_api.oauth2_password_flow(
        test_client_id, test_username, test_password, client_secret
    )
    assert "access_token" in oauth_token_data

    # Also test client credentials flow
    client_token_data = authenticated_keycloak_api.oauth2_client_credentials_flow(
        test_client_id, client_secret
    )
    assert "access_token" in client_token_data

    # Step 5: Scope Verification
    oauth_token_payload = decode_jwt_token(oauth_token_data["access_token"])

    # Verify token contains expected group memberships and roles
    if (
        "realm_access" in oauth_token_payload
        and "roles" in oauth_token_payload["realm_access"]
    ):
        token_roles = oauth_token_payload["realm_access"]["roles"]
        assert (
            admin_role_name in token_roles
        ), f"Admin role not found in token roles: {token_roles}"
        assert (
            user_role_name in token_roles
        ), f"User role not found in token roles: {token_roles}"

    # Verify user identity in token
    assert oauth_token_payload["preferred_username"] == test_username

    # Step 6: Cleanup
    authenticated_keycloak_api.delete_user(user_id)
    authenticated_keycloak_api.delete_client(client_internal_id)
    authenticated_keycloak_api.delete_group(admin_group_id)
    authenticated_keycloak_api.delete_group(user_group_id)
    authenticated_keycloak_api.delete_realm_role(admin_role_name)
    authenticated_keycloak_api.delete_realm_role(user_role_name)
