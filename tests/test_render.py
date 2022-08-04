import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from qhub.render import render_template, set_env_vars_in_config

from .conftest import PRESERVED_DIR, render_config_partial


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


def test_exists_after_render(write_qhub_config_to_file):
    items_to_check = [
        ".gitignore",
        "stages",
        "qhub-config.yaml",
        PRESERVED_DIR,
    ]

    qhub_config_loc, _ = write_qhub_config_to_file

    yaml = YAML()
    qhub_config_json = yaml.load(qhub_config_loc.read_text())

    # list of files/dirs available after `qhub render` command
    ls = os.listdir(Path(qhub_config_loc).parent.resolve())

    cicd = qhub_config_json.get("ci_cd", {}).get("type", None)

    if cicd == "github-actions":
        items_to_check.append(".github")
    elif cicd == "gitlab-ci":
        items_to_check.append(".gitlab-ci.yml")

    for i in items_to_check:
        assert i in ls
