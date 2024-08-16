import pytest

from tests.tests_deployment.keycloak_utils import delete_client_keycloak_test_roles
from tests.tests_deployment.utils import (
    get_jupyterhub_token,
    get_refresh_jupyterhub_token,
)


@pytest.fixture()
def cleanup_keycloak_roles():
    # setup
    yield
    # teardown
    delete_client_keycloak_test_roles(client_name="jupyterhub")
    delete_client_keycloak_test_roles(client_name="conda_store")


@pytest.fixture(scope="session")
def jupyterhub_access_token():
    return get_jupyterhub_token(note="base-jupyterhub-token")


@pytest.fixture(scope="function")
def refresh_token_response(request, jupyterhub_access_token):
    note = request.param  # Get the parameter passed to the fixture
    yield get_refresh_jupyterhub_token(jupyterhub_access_token, note)


def parameterized_fixture(new_note):
    """Utility function to create parameterized pytest fixtures."""
    return pytest.mark.parametrize(
        "refresh_token_response",
        [new_note],
        indirect=True,
    )


def token_parameterized(note):
    return parameterized_fixture(note)


@pytest.fixture(scope="function")
def access_token_response(refresh_token_response):
    yield refresh_token_response
