import pytest

import yaml

from qhub.render import render_default_template
from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, domain, cloud_provider, ci_provider, auth_provider",
    [
        ('do-pytest', 'do.qhub.dev', 'do', 'github-actions', 'github'),
        ('aws-pytest', 'aws.qhub.dev', 'aws', 'github-actions', 'github'),
        ('gcp-pytest', 'gcp.qhub.dev', 'gcp', 'github-actions', 'github'),
    ],
)
def test_render(project, domain, cloud_provider, ci_provider, auth_provider, tmp_path):
    config = render_config(
        project_name=project,
        qhub_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        repository='github.com/test/test',
        auth_provider=auth_provider,
        repository_auto_provision=False,
        auth_auto_provision=False,
        kubernetes_version='1.18.0',
        disable_prompt=True,
    )

    config_filename = tmp_path / (project + '.yaml')
    with open(config_filename, 'w') as f:
        yaml.dump(config, f)

    output_directory = tmp_path / "test"
    render_default_template(str(output_directory), config_filename)
