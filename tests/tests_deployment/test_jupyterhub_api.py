import pytest

from tests.tests_deployment import constants
from tests.tests_deployment.keycloak_utils import (
    assign_keycloak_client_role_to_user,
    create_keycloak_role,
)
from tests.tests_deployment.utils import create_jupyterhub_token, get_jupyterhub_session


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_roles_from_keycloak():
    session = get_jupyterhub_session()
    xsrf_token = session.cookies.get("_xsrf")
    response = session.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}",
        headers={"X-XSRFToken": xsrf_token},
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
    }


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
    component, scopes, expected_scopes_difference, cleanup_keycloak_roles
):
    # check token scopes before role creation and assignment
    token_response_before = create_jupyterhub_token(
        note="before-role-creation-and-assignment"
    )
    token_scopes_before = set(token_response_before.json()["scopes"])
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
    token_response_after = create_jupyterhub_token(
        note="after-role-creation-and-assignment"
    )
    token_scopes_after = set(token_response_after.json()["scopes"])
    # verify new scopes added/removed
    expected_scopes_difference = token_scopes_after - token_scopes_before
    # Comparing token scopes for the user before and after role assignment
    assert expected_scopes_difference == expected_scopes_difference


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_groups_from_keycloak():
    session = get_jupyterhub_session()
    xsrf_token = session.cookies.get("_xsrf")
    response = session.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users/{constants.KEYCLOAK_USERNAME}",
        headers={"X-XSRFToken": xsrf_token},
        verify=False,
    )
    user = response.json()
    assert set(user["groups"]) == {"/analyst", "/developer", "/users"}
