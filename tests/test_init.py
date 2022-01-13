import pytest

from .conftest import render_config_partial


@pytest.mark.parametrize(
    "k8s_version, expected", [(None, True), ("1.19", True), (1000, ValueError)]
)
def test_init(setup_fixture, k8s_version, expected):
    (qhub_config_loc, render_config_inputs) = setup_fixture
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    # pass "unsupported" kubernetes version to `render_config`
    # resulting in a `ValueError`
    if type(expected) == type and issubclass(expected, Exception):
        with pytest.raises(expected):
            render_config_partial(
                project_name=project,
                namespace=namespace,
                qhub_domain=domain,
                cloud_provider=cloud_provider,
                ci_provider=ci_provider,
                auth_provider=auth_provider,
                kubernetes_version=k8s_version,
            )
    else:
        render_config_partial(
            project_name=project,
            namespace=namespace,
            qhub_domain=domain,
            cloud_provider=cloud_provider,
            ci_provider=ci_provider,
            auth_provider=auth_provider,
            kubernetes_version=k8s_version,
        )
