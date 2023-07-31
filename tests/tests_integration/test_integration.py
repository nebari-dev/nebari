import re

import pytest
import requests

from tests.common.playwright_fixtures import navigator_parameterized
from tests.common.run_notebook import Notebook
from tests.tests_integration.deployment_fixtures import ignore_warnings, on_cloud


@pytest.fixture(autouse=True)
def disable_warnings():
    ignore_warnings()


@on_cloud("aws")
@navigator_parameterized(instance_name="gpu-instance")
def test_gpu(deploy, navigator, test_data_root):
    test_app = Notebook(navigator=navigator)
    notebook_name = "test_gpu.ipynb"
    notebook_path = test_data_root / notebook_name
    assert notebook_path.exists()
    with open(notebook_path, "r") as notebook:
        test_app.nav.write_file(filepath=notebook_name, content=notebook.read())
    expected_outputs = [
        re.compile(".*\n.*\n.*NVIDIA-SMI.*CUDA Version"),
        "True"
    ]
    test_app.run(
        path=notebook_name,
        expected_outputs=expected_outputs,
        conda_env="conda-env-nebari-git-nebari-git-gpu-py",
        runtime=60000,
        exact_match=False
    )


@on_cloud()
def test_service_status(deploy):
    """Tests if deployment on DigitalOcean succeeds"""
    service_urls = deploy["stages/07-kubernetes-services"]["service_urls"]["value"]
    assert (
        requests.get(service_urls["jupyterhub"]["health_url"], verify=False).status_code
        == 200
    )
    assert (
        requests.get(service_urls["keycloak"]["health_url"], verify=False).status_code
        == 200
    )
    assert (
        requests.get(
            service_urls["dask_gateway"]["health_url"], verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(
            service_urls["conda_store"]["health_url"], verify=False
        ).status_code
        == 200
    )
    assert (
        requests.get(service_urls["monitoring"]["health_url"], verify=False).status_code
        == 200
    )


@on_cloud()
def test_verify_keycloak_users(deploy):
    """Tests if keycloak is working and it has expected users"""
    keycloak_credentials = deploy["stages/05-kubernetes-keycloak"][
        "keycloak_credentials"
    ]["value"]
    from keycloak import KeycloakAdmin

    keycloak_admin = KeycloakAdmin(
        server_url=f"{keycloak_credentials['url']}/auth/",
        username=keycloak_credentials["username"],
        password=keycloak_credentials["password"],
        realm_name=keycloak_credentials["realm"],
        client_id=keycloak_credentials["client_id"],
        verify=False,
    )
    assert set([u["username"] for u in keycloak_admin.get_users()]) == {
        "nebari-bot",
        "read-only-user",
        "root",
    }
