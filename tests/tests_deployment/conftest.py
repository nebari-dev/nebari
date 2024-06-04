import pytest

from tests.tests_deployment.keycloak_utils import delete_client_keycloak_test_roles


@pytest.fixture()
def cleanup_keycloak_roles():
    # setup
    yield
    # teardown
    delete_client_keycloak_test_roles(client_name="jupyterhub")
