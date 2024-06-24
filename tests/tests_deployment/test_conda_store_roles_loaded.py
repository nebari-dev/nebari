import pytest

from tests.common.conda_store_utils import get_conda_store_user_permissions
from tests.tests_deployment import constants
from tests.tests_deployment.keycloak_utils import (
    assign_keycloak_client_role_to_user,
    create_keycloak_role,
)


@pytest.mark.parametrize(
    "scopes,changed_scopes",
    (
        [
            "admin!namespace=analyst,developer!namespace=nebari-git",
            {"nebari-git/*": ["developer"], "analyst/*": ["admin"]},
        ],
        [
            "admin!namespace=analyst,developer!namespace=invalid-namespace",
            {"analyst/*": ["admin"]},
        ],
        [
            # duplicate namespace role, chose highest permissions
            "admin!namespace=analyst,developer!namespace=analyst",
            {"analyst/*": ["admin"]},
        ],
        ["invalid-role!namespace=analyst", {}],
    ),
)
@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
@pytest.mark.filterwarnings(
    "ignore:.*auto_refresh_token is deprecated:DeprecationWarning"
)
@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_conda_store_roles_loaded_from_keycloak(
    scopes: str, changed_scopes: dict, cleanup_keycloak_roles
):

    # Verify permissions/roles are different from what we're about to set
    # So that this test is actually testing the change
    permissions = get_conda_store_user_permissions()
    entity_roles = permissions["data"]["entity_roles"]
    for namespace, role in changed_scopes.items():
        assert entity_roles[namespace] != role

    role = create_keycloak_role(
        client_name="conda_store",
        # Note: we're clearing this role after every test case, and we're clearing
        # it by name, so it must start with test- to be deleted afterwards
        role_name="test-custom-role",
        scopes=scopes,
        component="conda-store",
    )
    assert role
    # assign created role to the user
    assign_keycloak_client_role_to_user(
        constants.KEYCLOAK_USERNAME, client_name="conda_store", role=role
    )
    permissions = get_conda_store_user_permissions()
    updated_entity_roles = permissions["data"]["entity_roles"]

    # Verify permissions/roles are set to expectation
    assert updated_entity_roles == {
        **entity_roles,
        **changed_scopes,
    }
