"""Keycloak API tests for roles, groups, and integration workflows."""

import uuid

import pytest

from .keycloak_api_utils import KeycloakAPI, decode_jwt_token

# Import fixtures from test_keycloak_api
pytest_plugins = ["tests.tests_deployment.test_keycloak_api"]


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
    assert response.status_code == 201, f"Failed to create realm role: {response.text}"

    # Verify role was created
    get_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert get_response.status_code == 200
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

    assert response.status_code == 200, f"Failed to list realm roles: {response.text}"
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
    assert create_response.status_code == 201

    # Get the role by name
    response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert response.status_code == 200

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
    assert create_response.status_code == 201

    # Delete the role
    delete_response = authenticated_keycloak_api.delete_realm_role(test_role_name)
    assert delete_response.status_code == 204

    # Verify role is deleted
    get_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    assert get_response.status_code == 404


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
    assert create_client_response.status_code == 201

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
    assert role_response.status_code == 201

    # Verify role was created
    get_role_response = authenticated_keycloak_api.get_client_role_by_name(
        client_internal_id, test_role_name
    )
    assert get_role_response.status_code == 200
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
    assert create_response.status_code == 201

    # Get client internal ID
    get_response = authenticated_keycloak_api.get_clients(client_id=test_client_id)
    client_internal_id = get_response.json()[0]["id"]

    # Get client roles
    roles_response = authenticated_keycloak_api.get_client_roles(client_internal_id)
    assert roles_response.status_code == 200
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
    assert create_role_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign role to user
    assign_response = authenticated_keycloak_api.assign_realm_roles_to_user(
        user_id, [role]
    )
    assert assign_response.status_code == 204

    # Verify user has role
    user_roles_response = authenticated_keycloak_api.get_user_realm_roles(user_id)
    assert user_roles_response.status_code == 200
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
    assert create_client_response.status_code == 201

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
    assert create_role_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign client role to user
    assign_response = authenticated_keycloak_api.assign_client_roles_to_user(
        user_id, client_internal_id, [role]
    )
    assert assign_response.status_code == 204

    # Verify user has client role
    user_roles_response = authenticated_keycloak_api.get_user_client_roles(
        user_id, client_internal_id
    )
    assert user_roles_response.status_code == 200
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
    assert create_role_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Assign role to user
    assign_response = authenticated_keycloak_api.assign_realm_roles_to_user(
        user_id, [role]
    )
    assert assign_response.status_code == 204

    # Remove role from user
    remove_response = authenticated_keycloak_api.remove_realm_roles_from_user(
        user_id, [role]
    )
    assert remove_response.status_code == 204

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
    assert response.status_code == 201, f"Failed to create group: {response.text}"

    # Verify group was created
    groups_response = authenticated_keycloak_api.get_groups()
    assert groups_response.status_code == 200
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

    assert response.status_code == 200, f"Failed to list groups: {response.text}"
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
    assert create_group_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_response.status_code == 204

    # Verify user is in group
    user_groups_response = authenticated_keycloak_api.get_user_groups(user_id)
    assert user_groups_response.status_code == 200
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
    assert create_group_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_response.status_code == 204

    # Remove user from group
    remove_response = authenticated_keycloak_api.remove_user_from_group(
        user_id, group_id
    )
    assert remove_response.status_code == 204

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
    assert create_response.status_code == 201

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Delete the group
    delete_response = authenticated_keycloak_api.delete_group(group_id)
    assert delete_response.status_code == 204

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
    assert create_role_response.status_code == 201

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(test_role_name)
    role = role_response.json()

    # Create a group
    group_data = {"name": test_group_name}
    create_group_response = authenticated_keycloak_api.create_group(group_data)
    assert create_group_response.status_code == 201

    # Get group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    group = [g for g in groups if g["name"] == test_group_name][0]
    group_id = group["id"]

    # Assign role to group
    assign_role_response = authenticated_keycloak_api.assign_realm_roles_to_group(
        group_id, [role]
    )
    assert assign_role_response.status_code == 204

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to group
    add_user_response = authenticated_keycloak_api.add_user_to_group(user_id, group_id)
    assert add_user_response.status_code == 204

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
    assert create_role_response.status_code == 201

    # Get the role
    role_response = authenticated_keycloak_api.get_realm_role_by_name(role_name)
    role = role_response.json()

    # Create parent group
    parent_group_data = {"name": parent_group_name}
    create_parent_response = authenticated_keycloak_api.create_group(parent_group_data)
    assert create_parent_response.status_code == 201

    # Get parent group ID
    groups_response = authenticated_keycloak_api.get_groups()
    groups = groups_response.json()
    parent_group = [g for g in groups if g["name"] == parent_group_name][0]
    parent_group_id = parent_group["id"]

    # Assign role to parent group
    assign_role_response = authenticated_keycloak_api.assign_realm_roles_to_group(
        parent_group_id, [role]
    )
    assert assign_role_response.status_code == 204

    # Create child group under parent
    child_group_data = {"name": child_group_name}
    create_child_response = authenticated_keycloak_api.create_subgroup(
        parent_group_id, child_group_data
    )
    assert create_child_response.status_code == 201

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
    assert create_user_response.status_code == 201

    # Get user ID
    user_get_response = authenticated_keycloak_api.get_users(username=test_username)
    user_id = user_get_response.json()[0]["id"]

    # Add user to child group
    add_user_response = authenticated_keycloak_api.add_user_to_group(
        user_id, child_group_id
    )
    assert add_user_response.status_code == 204

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
