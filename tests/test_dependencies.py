import re
import subprocess
from pathlib import Path

import pytest
import ruamel.yaml
import toml

from .conftest import TEST_CONDA_ENV_NAME

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


@pytest.mark.conda
def test_pyproject_dependencies(conda_env_file):
    """
    Populate a temporary environment.yaml, then attempt to create a conda environment with it.

    This test ensures that nebari can be packaged by and available on conda-forge.
    """

    template = {
        "name": TEST_CONDA_ENV_NAME,
        "channels": ["conda-forge"],
        "dependencies": [],
    }

    assert PYPROJECT.exists()

    with open(PYPROJECT, "r") as f:
        data = toml.load(f)

    for dep in data["project"].get("dependencies"):
        dep_details = re.split(r"([=><]{1,2})", dep)
        if len(dep_details) > 1:
            # split into package, constraint, version
            p, c, v = dep_details
        else:
            p = dep_details[0]
            c, v = "", ""

        # kubernetes package on conda-forge is prepended with "python-"
        if p == "kubernetes":
            p = "python-" + p

        template["dependencies"].append(f"{p}{c}{v}")

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
