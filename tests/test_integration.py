from tests.deployment_fixtures import on_cloud


@on_cloud("do")
def test_do_deployment(deploy):
    """Tests if deployment on DigitalOcean succeeds"""
    assert True
