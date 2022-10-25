import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from nebari.render import render_template, set_env_vars_in_config

from .conftest import PRESERVED_DIR, render_config_partial


@pytest.fixture
def write_nebari_config_to_file(setup_fixture):
    nebari_config_loc, render_config_inputs = setup_fixture
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
        nebari_domain=domain,
        cloud_provider=cloud_provider,
        ci_provider=ci_provider,
        auth_provider=auth_provider,
        kubernetes_version=None,
    )

    # write to nebari_config.yaml
    yaml = YAML(typ="unsafe", pure=True)
    yaml.dump(config, nebari_config_loc)

    render_template(str(nebari_config_loc.parent), nebari_config_loc, force=True)

    yield setup_fixture


def test_get_secret_config_entries(monkeypatch):
    sec1 = "secret1"
    sec2 = "nestedsecret1"
    config_orig = {
        "key1": "value1",
        "key2": "NEBARI_SECRET_secret_val",
        "key3": {
            "nested_key1": "nested_value1",
            "nested_key2": "NEBARI_SECRET_nested_secret_val",
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


def test_render_template(write_nebari_config_to_file):
    nebari_config_loc, render_config_inputs = write_nebari_config_to_file
    (
        project,
        namespace,
        domain,
        cloud_provider,
        ci_provider,
        auth_provider,
    ) = render_config_inputs

    yaml = YAML()
    nebari_config_json = yaml.load(nebari_config_loc.read_text())

    assert nebari_config_json["project_name"] == project
    assert nebari_config_json["namespace"] == namespace
    assert nebari_config_json["domain"] == domain
    assert nebari_config_json["provider"] == cloud_provider


def test_exists_after_render(write_nebari_config_to_file):
    items_to_check = [
        ".gitignore",
        "stages",
        "nebari-config.yaml",
        PRESERVED_DIR,
    ]

    nebari_config_loc, _ = write_nebari_config_to_file

    yaml = YAML()
    nebari_config_json = yaml.load(nebari_config_loc.read_text())

    # list of files/dirs available after `nebari render` command
    ls = os.listdir(Path(nebari_config_loc).parent.resolve())

    cicd = nebari_config_json.get("ci_cd", {}).get("type", None)

    if cicd == "github-actions":
        items_to_check.append(".github")
    elif cicd == "gitlab-ci":
        items_to_check.append(".gitlab-ci.yml")

    for i in items_to_check:
        assert i in ls
