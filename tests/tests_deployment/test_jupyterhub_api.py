import uuid

import pytest

from tests.tests_deployment import constants
from tests.tests_deployment.utils import get_jupyterhub_session, get_jupyterhub_token, create_jupyterhub_token
from tests.tests_deployment.keycloak_utils import create_keycloak_role, assign_keycloak_client_role_to_user


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


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings("ignore:.*auto_refresh_token is deprecated:DeprecationWarning")
def test_keycloak_roles_attributes_parsed_as_jhub_scopes(cleanup_keycloak_roles):
    # check token scopes before role creation and assignment
    response_before = create_jupyterhub_token(note="before-scope-parsing-test")
    # create keycloak role with jupyterhub scopes in attributes
    role = create_keycloak_role(
        client_name="jupyterhub",
        # Note: we're clearing this role after every test case, and we're clearing
        # it by name, so it must start with test- to be deleted afterward
        role_name=f"test-custom-role",
        scopes="read:users:shares,read:groups:shares,users:shares",
        component="jupyterhub"
    )
    assert role
    # assign created role to the user
    assign_keycloak_client_role_to_user(constants.KEYCLOAK_USERNAME, client_name="jupyterhub", role=role)
    response_after = create_jupyterhub_token(note="after-role-parsing")
    # verify new scopes added/removed
    scopes_difference = set(response_after.json()['scopes']) - set(response_before.json()['scopes'])
    assert scopes_difference == {
        'read:groups:shares',
        'users:shares',
        'read:users:shares',
    }


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
