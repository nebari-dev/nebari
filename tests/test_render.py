import pytest

from ruamel import yaml

from qhub.render import render_default_template
from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, namespace, domain, cloud_provider, ci_provider, auth_provider",
    [
        ("do-pytest", "dev", "do.qhub.dev", "do", "github-actions", "github"),
        ("aws-pytest", "dev", "aws.qhub.dev", "aws", "github-actions", "github"),
        ("gcp-pytest", "dev", "gcp.qhub.dev", "gcp", "github-actions", "github"),
        ("azure-pytest", "dev", "azure.qhub.dev", "azure", "github-actions", "github"),
    ],
)
def test_render(project, namespace, domain, cloud_provider, ci_provider, auth_provider, tmp_path):
    config = render_config(
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

    config_filename = tmp_path / (project + ".yaml")
    with open(config_filename, "w") as f:
        yaml.dump(config, f)

    output_directory = tmp_path / "test"
    render_default_template(str(output_directory), config_filename)
