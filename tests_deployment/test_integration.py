import requests

from tests_deployment.deployment_fixtures import on_cloud


@on_cloud("do")
def test_do_deployment(deploy):
    """Tests if deployment on DigitalOcean succeeds"""
    service_urls = deploy['stages/07-kubernetes-services']['service_urls']['value']
    assert requests.get(service_urls["jupyterhub"]['health_url'], verify=False).status_code == 200
    assert requests.get(service_urls["keycloak"]['health_url'], verify=False).status_code == 200
    assert requests.get(service_urls["dask_gateway"]['health_url'], verify=False).status_code == 200
    assert requests.get(service_urls["conda_store"]['health_url'], verify=False).status_code == 200
    assert requests.get(service_urls["monitoring"]['health_url'], verify=False).status_code == 200
