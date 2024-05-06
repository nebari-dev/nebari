import pytest

from tests.tests_deployment import constants
from tests.tests_deployment.utils import get_jupyterhub_session


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
