import pytest

import qhub.schema
from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, terraform_version, domain, cloud_provider, ci_provider, oauth_provider",
    [
        ("do-pytest", "0.13.5", "do.qhub.dev", "do", "github-actions", "github"),
        ("aws-pytest", "0.13.5", "aws.qhub.dev", "aws", "github-actions", "github"),
        ("gcp-pytest", "0.13.5", "gcp.qhub.dev", "gcp", "github-actions", "github"),
    ],
)
def test_schema(
    project, terraform_version, domain, cloud_provider, ci_provider, oauth_provider
):
    config = render_config(
        project_name=project,
        terraform_version=terraform_version,
        qhub_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        repository="github.com/test/test",
        repository_auto_provision=False,
        oauth_provider=oauth_provider,
        oauth_auto_provision=False,
        disable_prompt=True,
    )
    assert qhub.schema.verify(config) is None
