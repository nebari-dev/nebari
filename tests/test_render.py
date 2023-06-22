import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from _nebari.render import render_template
from _nebari.stages.base import get_available_stages

from .conftest import PRESERVED_DIR


@pytest.fixture
def write_nebari_config_to_file(setup_fixture, render_config_partial):
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

    stages = get_available_stages()
    render_template(str(nebari_config_loc.parent), config, stages)

    yield setup_fixture


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
