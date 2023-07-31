import re

from tests.common.playwright_fixtures import navigator_parameterized
from tests.common.run_notebook import Notebook
from tests.tests_integration.deployment_fixtures import on_cloud


# @on_cloud("aws")
@navigator_parameterized(instance_name="gpu-instance")
def test_gpu(navigator, test_data_root):
    test_app = Notebook(navigator=navigator)
    notebook_name = "test_gpu.ipynb"
    notebook_path = test_data_root / notebook_name
    assert notebook_path.exists()
    with open(notebook_path, "r") as notebook:
        test_app.nav.write_file(filepath=notebook_name, content=notebook.read())
    expected_outputs = [
        re.compile(".*\n.*\n.*NVIDIA-SMI.*CUDA Version"),
        "True"
    ]
    test_app.run(
        path=notebook_name,
        expected_outputs=expected_outputs,
        conda_env="conda-env-nebari-git-nebari-git-gpu-py",
        runtime=60000,
        exact_match=False
    )
