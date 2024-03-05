import base64

import requests

from tests.tests_deployment import constants


def test_grafana_api_not_accessible_with_default_credentials():
    """Making sure that Grafana's API is not accessible on default user/pass"""
    user_pass_b64_encoded = base64.b64encode(b"admin:prom-operator").decode()
    response = requests.get(
        f"https://{constants.NEBARI_HOSTNAME}/monitoring/api/datasources",
        headers={"Authorization": f"Basic {user_pass_b64_encoded}"},
    )
    assert response.status_code == 401
