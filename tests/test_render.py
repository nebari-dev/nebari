import pytest

from ruamel.yaml import YAML

from qhub.render import render_template, set_env_vars_in_config, remove_existing_renders
from qhub.initialize import render_config

INIT_INPUTS = [
    # project, namespace, domain, cloud_provider, ci_provider, auth_provider
    ("do-pytest", "dev", "do.qhub.dev", "do", "github-actions", "github"),
    ("aws-pytest", "dev", "aws.qhub.dev", "aws", "github-actions", "github"),
    ("gcp-pytest", "dev", "gcp.qhub.dev", "gcp", "github-actions", "github"),
    ("azure-pytest", "dev", "azure.qhub.dev", "azure", "github-actions", "github"),
]
QHUB_CONFIG_FN = "qhub-config.yaml"
PRESERVED_DIR = "preserved_dir"


@pytest.fixture
def init_render(request, tmp_path):
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = request.param

    output_directory = tmp_path / f"{cloud_provider}_output_dir"
    output_directory.mkdir()
    qhub_config = output_directory / QHUB_CONFIG_FN

    # data that should NOT be deleted when `qhub render` is called
    preserved_directory = output_directory / PRESERVED_DIR
    preserved_directory.mkdir()
    preserved_filename = preserved_directory / "file.txt"
    preserved_filename.write_text("This is a test...")

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
    yaml = YAML(typ="unsafe", pure=True)
    yaml.dump(config, qhub_config)

    render_template(str(output_directory), qhub_config, force=True)

    yield (output_directory, request)


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


@pytest.mark.parametrize(
    "init_render",
    INIT_INPUTS,
    indirect=True,
)
def test_render_template(init_render):
    output_directory, request = init_render
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = request.param
    qhub_config = output_directory / QHUB_CONFIG_FN

    yaml = YAML()
    qhub_config_json = yaml.load(qhub_config.read_text())

    assert qhub_config_json["project_name"] == project
    assert qhub_config_json["namespace"] == namespace
    assert qhub_config_json["domain"] == domain
    assert qhub_config_json["provider"] == cloud_provider


@pytest.mark.parametrize(
    "init_render",
    INIT_INPUTS,
    indirect=True,
)
def test_remove_existing_renders(init_render):
    output_directory, request = init_render
    dirs = [_.name for _ in output_directory.iterdir()]
    preserved_files = [_ for _ in (output_directory / PRESERVED_DIR).iterdir()]

    # test `remove_existing_renders` implicitly
    assert PRESERVED_DIR in dirs
    assert len(preserved_files[0].read_text()) > 0

    # test `remove_existing_renders` explicitly
    remove_existing_renders(output_directory)

    assert PRESERVED_DIR in dirs
    assert len(preserved_files[0].read_text()) > 0
