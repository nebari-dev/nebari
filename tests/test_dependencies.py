import subprocess
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).parent.parent
PYPROJECT = SRC_DIR / "pyproject.toml"


@pytest.mark.conda
def test_build_by_conda_forge(tmp_path):
    """
    This test ensures that nebari can be built and packaged by conda-forge.

    This is achieved by walking through the following steps:
      1. Use Python build package to generate the `sdist` .tar.gz file
      2. Use grayskull package to generate the `meta.yaml` recipe file
      3. Use conda build to attempt to build the nebari package from the `meta.yaml`

    These steps mimic what takes places on the conda-forge/nebari-feedstock repo whenever
    a new version of the package gets released.

    NOTE: this test requires conda and conda-build
    """

    assert PYPROJECT.exists()

    try:
        # build sdist
        subprocess.run(
            ["python", "-m", "build", SRC_DIR, "--outdir", tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # get location of sdist file built above
        sdist_loc = next(tmp_path.glob("*.tar.gz"))
        # run grayskull to create the meta.yaml using the local sdist file
        subprocess.run(
            [
                "grayskull",
                "pypi",
                "--strict-conda-forge",
                sdist_loc,
                "--output",
                tmp_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # get the directory the meta.yaml is in
        meta_loc = tmp_path / "nebari"
        # try to run conda build to build package from meta.yaml
        subprocess.run(
            ["conda", "build", meta_loc],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode("utf-8"))
        raise e
