import pytest

import qhub.schema
from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, domain, cloud_provider, ci_provider, oauth_provider",
    [
        ('do-pytest', 'do.qhub.dev', 'do', 'github-actions', 'github'),
        ('aws-pytest', 'aws.qhub.dev', 'aws', 'github-actions', 'github'),
        ('gcp-pytest', 'gcp.qhub.dev', 'gcp', 'github-actions', 'github'),
    ],
)
def test_schema(project, domain, cloud_provider, ci_provider, oauth_provider):
    config = render_config(
        project_name=project,
        qhub_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        repository='github.com/test/test',
        repository_auto_provision=False,
        oauth_provider=oauth_provider,
        oauth_auto_provision=False,
        disable_prompt=True,
    )
    assert qhub.schema.verify(config) is None
