import qhub.schema

from .conftest import render_config_partial


def test_schema(setup_fixture):
    (qhub_config_loc, render_config_inputs) = setup_fixture
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    config = render_config_partial(
        project_name=project,
        namespace=namespace,
        qhub_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        auth_provider=auth_provider,
        kubernetes_version=None,
    )

    qhub.schema.verify(config)
