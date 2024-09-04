import pytest
import requests

from tests.tests_deployment import constants
from tests.tests_deployment.conftest import token_parameterized
from tests.tests_deployment.keycloak_utils import (
    assign_keycloak_client_role_to_user,
    create_keycloak_role,
    get_keycloak_client_details_by_name,
    get_keycloak_client_role,
    get_keycloak_client_roles,
    get_keycloak_role_groups,
)
from tests.tests_deployment.utils import get_refresh_jupyterhub_token


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_roles_from_keycloak(jupyterhub_access_token):
    response = requests.get(
        url=f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}",
        headers={"Authorization": f"Bearer {jupyterhub_access_token}"},
        verify=False,
    )
    user = response.json()
    assert set(user["roles"]) == {
        "user",
        "manage-account",
        "jupyterhub_developer",
        "argo-developer",
        "dask_gateway_developer",
        "grafana_viewer",
        "conda_store_developer",
        "argo-viewer",
        "grafana_developer",
        "manage-account-links",
        "view-profile",
        # default roles
        "allow-read-access-to-services-role",
        "allow-group-directory-creation-role",
    }


@token_parameterized(note="get-default-scopes")
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_default_user_role_scopes(access_token_response):
    token_scopes = set(access_token_response.json()["scopes"])
    assert "read:services" in token_scopes


@pytest.mark.filterwarnings(
    "ignore:.*auto_refresh_token is deprecated:DeprecationWarning"
)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_check_default_roles_added_in_keycloak():
    client_roles = get_keycloak_client_roles(client_name="jupyterhub")
    role_names = [role["name"] for role in client_roles]
    assert "allow-app-sharing-role" in role_names
    assert "allow-read-access-to-services-role" in role_names
    assert "allow-group-directory-creation-role" in role_names


@pytest.mark.filterwarnings(
    "ignore:.*auto_refresh_token is deprecated:DeprecationWarning"
)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_check_directory_creation_scope_attributes():
    client_role = get_keycloak_client_role(
        client_name="jupyterhub", role_name="allow-group-directory-creation-role"
    )
    assert client_role["attributes"]["component"][0] == "shared-directory"
    assert client_role["attributes"]["scopes"][0] == "write:shared-mount"


@pytest.mark.filterwarnings(
    "ignore:.*auto_refresh_token is deprecated:DeprecationWarning"
)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_groups_with_mount_permissions():
    client_role = get_keycloak_client_role(
        client_name="jupyterhub", role_name="allow-group-directory-creation-role"
    )
    client_details = get_keycloak_client_details_by_name(client_name="jupyterhub")
    role_groups = get_keycloak_role_groups(
        client_id=client_details["id"], role_name=client_role["name"]
    )
    assert set([group["path"] for group in role_groups]) == set(
        [
            "/developer",
            "/admin",
            "/analyst",
        ]
    )


@token_parameterized(note="before-role-creation-and-assignment")
@pytest.mark.parametrize(
    "component,scopes,expected_scopes_difference",
    (
        [
            "jupyterhub",
            "read:users:shares,read:groups:shares,users:shares",
            {"read:groups:shares", "users:shares", "read:users:shares"},
        ],
        ["invalid-component", "read:users:shares,read:groups:shares,users:shares", {}],
        ["invalid-component", "admin:invalid-scope", {}],
    ),
)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings(
    "ignore:.*auto_refresh_token is deprecated:DeprecationWarning"
)
def test_keycloak_roles_attributes_parsed_as_jhub_scopes(
    component,
    scopes,
    expected_scopes_difference,
    cleanup_keycloak_roles,
    access_token_response,
):
    # check token scopes before role creation and assignment
    token_scopes_before = set(access_token_response.json()["scopes"])
    # create keycloak role with jupyterhub scopes in attributes
    role = create_keycloak_role(
        client_name="jupyterhub",
        # Note: we're clearing this role after every test case, and we're clearing
        # it by name, so it must start with test- to be deleted afterward
        role_name="test-custom-role",
        scopes=scopes,
        component=component,
    )
    assert role
    # assign created role to the user
    assign_keycloak_client_role_to_user(
        constants.KEYCLOAK_USERNAME, client_name="jupyterhub", role=role
    )
    token_response_after = get_refresh_jupyterhub_token(
        old_token=access_token_response.json()["token"],
        note="after-role-creation-and-assignment",
    )
    token_scopes_after = set(token_response_after.json()["scopes"])
    # verify new scopes added/removed
    expected_scopes_difference = token_scopes_after - token_scopes_before
    # Comparing token scopes for the user before and after role assignment
    assert expected_scopes_difference == expected_scopes_difference


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_groups_from_keycloak(jupyterhub_access_token):
    response = requests.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}",
        headers={"Authorization": f"Bearer {jupyterhub_access_token}"},
        verify=False,
    )
    user = response.json()
    assert set(user["groups"]) == {"/analyst", "/developer", "/users"}
