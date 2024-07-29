import pytest

from _nebari.constants import AWS_DEFAULT_REGION
from _nebari.initialize import render_config
from _nebari.stages.bootstrap import CiEnum
from _nebari.stages.kubernetes_keycloak import AuthenticationEnum
from nebari.schema import ProviderEnum


@pytest.mark.parametrize(
    "k8s_version, cloud_provider, expected",
    [
        (None, ProviderEnum.aws, "1.20"),
        ("1.19", ProviderEnum.aws, "1.19"),
    ],
)
def test_render_config(mock_all_cloud_methods, k8s_version, cloud_provider, expected):
    if type(expected) is type and issubclass(expected, Exception):
        with pytest.raises(expected):
            config = render_config(
                project_name="test",
                namespace="dev",
                nebari_domain="test.dev",
                cloud_provider=cloud_provider,
                region=AWS_DEFAULT_REGION,
                ci_provider=CiEnum.none,
                auth_provider=AuthenticationEnum.password,
                kubernetes_version=k8s_version,
            )
            assert config
    else:
        config = render_config(
            project_name="test",
            namespace="dev",
            nebari_domain="test.dev",
            cloud_provider=cloud_provider,
            region=AWS_DEFAULT_REGION,
            ci_provider=CiEnum.none,
            auth_provider=AuthenticationEnum.password,
            kubernetes_version=k8s_version,
        )

        assert (
            config.get("amazon_web_services", {}).get("kubernetes_version") == expected
        )

    assert config["project_name"] == "test"
