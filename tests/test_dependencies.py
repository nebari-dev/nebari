import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import ruamel.yaml

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"
CONDA_ENV_NAME = "nebari-test-dependencies"


@pytest.fixture
def conda_env_file(tmp_path):
    """Create a temporary environment.yaml file."""

    yield tmp_path / "environment.yaml"

    # remove created conda environment
    try:
        subprocess.run(
            ["conda", "env", "remove", "-n", CONDA_ENV_NAME, "-y"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise e


def test_pyproject_dependencies(conda_env_file):
    """
    Populate a temporary environment.yaml, then attempt to create a conda environment with it.

    This test ensures that nebari can be packaged by and available on conda-forge.
    """

    template = {"name": CONDA_ENV_NAME, "channels": ["conda-forge"], "dependencies": []}

    assert PYPROJECT.exists()

    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)

    for dep in data["project"].get("dependencies"):
        # split into package, constraint, version
        p, c, v = re.split(r"([=><]{1,2})", dep)
        template["dependencies"].append(f"{p} {c}{v}")

    with open(conda_env_file, "w+") as f:
        yaml = ruamel.yaml.YAML()
        yaml.indent(sequence=4, offset=2)
        yaml.dump(template, f)

    try:
        subprocess.run(
            ["conda", "env", "create", "-f", conda_env_file],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise e
