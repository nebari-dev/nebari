import pytest

from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, namespace, domain, cloud_provider, ci_provider, auth_provider",
    [
        ("pytest-do", "dev", "do.qhub.dev", "do", "github-actions", "github"),
        ("pytest-aws", "dev", "aws.qhub.dev", "aws", "github-actions", "github"),
        ("pytest-gcp", "dev", "gcp.qhub.dev", "gcp", "github-actions", "github"),
        ("pytest-azure", "dev", "azure.qhub.dev", "azure", "github-actions", "github"),
    ],
)
def test_init(project, namespace, domain, cloud_provider, ci_provider, auth_provider):
    render_config(
        project_name=project,
        namespace=namespace,
        qhub_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        repository="github.com/test/test",
        auth_provider=auth_provider,
        repository_auto_provision=False,
        auth_auto_provision=False,
        terraform_state="remote",
        kubernetes_version="1.18.0",
        disable_prompt=True,
    )
