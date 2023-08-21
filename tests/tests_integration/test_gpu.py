import re

import pytest

from tests.common.playwright_fixtures import navigator_parameterized
from tests.common.run_notebook import Notebook
from tests.tests_integration.deployment_fixtures import on_cloud


@on_cloud(["aws", "gcp"])
@pytest.mark.gpu
@navigator_parameterized(instance_name="gpu-instance")
def test_gpu(deploy, navigator, test_data_root):
    test_app = Notebook(navigator=navigator)
    conda_env = "gpu"
    test_app.create_notebook(
        conda_env=f"conda-env-nebari-git-nebari-git-{conda_env}-py"
    )
    test_app.assert_code_output(
        code="!nvidia-smi",
        expected_output=re.compile(".*\n.*\n.*NVIDIA-SMI.*CUDA Version"),
    )

    test_app.assert_code_output(
        code="import torch;torch.cuda.is_available()", expected_output="True"
    )
