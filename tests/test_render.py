import pytest

from ruamel import yaml

from qhub.render import render_template, set_env_vars_in_config
from qhub.initialize import render_config


@pytest.mark.parametrize(
    "project, namespace, domain, cloud_provider, ci_provider, auth_provider",
    [
        ("pytest-do", "dev", "do.qhub.dev", "do", "github-actions", "github"),
        ("pytest-aws", "dev", "aws.qhub.dev", "aws", "github-actions", "github"),
        ("pytest-gcp", "dev", "gcp.qhub.dev", "gcp", "github-actions", "github"),
        ("pytestazure", "dev", "azure.qhub.dev", "azure", "github-actions", "github"),
    ],
)
def test_render(
    project, namespace, domain, cloud_provider, ci_provider, auth_provider, tmp_path
):
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
    render_template(str(output_directory), config_filename, force=True)


def test_get_secret_config_entries(monkeypatch):
    sec1 = "secret1"
    sec2 = "nestedsecret1"
    config_orig = {
        "key1": "value1",
        "key2": "QHUB_SECRET_secret_val",
        "key3": {
            "nested_key1": "nested_value1",
            "nested_key2": "QHUB_SECRET_nested_secret_val",
        },
    }
    expected = {
        "key1": "value1",
        "key2": sec1,
        "key3": {
            "nested_key1": "nested_value1",
            "nested_key2": sec2,
        },
    }

    # should raise error if implied env var is not set
    with pytest.raises(EnvironmentError):
        config = config_orig.copy()
        set_env_vars_in_config(config)

    monkeypatch.setenv("secret_val", sec1, prepend=False)
    monkeypatch.setenv("nested_secret_val", sec2, prepend=False)
    config = config_orig.copy()
    set_env_vars_in_config(config)
    assert config == expected
