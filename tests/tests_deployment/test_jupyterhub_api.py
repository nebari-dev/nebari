import pytest
import requests

from tests.tests_deployment import constants
from tests.tests_deployment.utils import get_jupyterhub_token


@pytest.fixture(scope="session")
def api_token():
    return get_jupyterhub_token("jupyterhub-api")


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_roles_from_keycloak(api_token):
    response = requests.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users",
        headers={"Authorization": f"Bearer {api_token}"},
        verify=False,
    )
    users = response.json()
    print(users)
    assert users[0]["roles"] == []
