import pytest

from tests.tests_deployment import constants


@pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")
def test_jupyterhub_loads_roles_from_keycloak():
    session = get_jupyterhub_session()
    xsrf_token = session.cookies.get("_xsrf")
    response = session.get(
        f"https://{constants.NEBARI_HOSTNAME}/hub/api/users",
        headers={"X-XSRFToken": xsrf_token},
        verify=False,
    )
    users = response.json()
    print(users)
    assert users[0]["roles"] == []
