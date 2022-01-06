import pytest

from ruamel.yaml import YAML

from qhub.render import render_template, set_env_vars_in_config, remove_existing_renders
from .conftest import render_config_partial, PRESERVED_DIR


@pytest.fixture
def write_qhub_config_to_file(setup_fixture):
    qhub_config_loc, render_config_inputs = setup_fixture
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

    # write to qhub_config.yaml
    yaml = YAML(typ="unsafe", pure=True)
    yaml.dump(config, qhub_config_loc)

    render_template(str(qhub_config_loc.parent), qhub_config_loc, force=True)

    yield setup_fixture


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


def test_render_template(write_qhub_config_to_file):
    qhub_config_loc, render_config_inputs = write_qhub_config_to_file
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    yaml = YAML()
    qhub_config_json = yaml.load(qhub_config_loc.read_text())

    assert qhub_config_json["project_name"] == project
    assert qhub_config_json["namespace"] == namespace
    assert qhub_config_json["domain"] == domain
    assert qhub_config_json["provider"] == cloud_provider


def test_remove_existing_renders(write_qhub_config_to_file):
    qhub_config_loc, _ = write_qhub_config_to_file
    output_directory = qhub_config_loc.parent
    dirs = [_.name for _ in output_directory.iterdir()]
    preserved_files = [_ for _ in (output_directory / PRESERVED_DIR).iterdir()]

    # test `remove_existing_renders` implicitly
    assert PRESERVED_DIR in dirs
    assert len(preserved_files[0].read_text()) > 0

    # test `remove_existing_renders` explicitly
    remove_existing_renders(output_directory)

    assert PRESERVED_DIR in dirs
    assert len(preserved_files[0].read_text()) > 0
