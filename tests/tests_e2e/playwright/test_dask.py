import re

from tests.common.playwright_fixtures import navigator_parameterized
from tests.common.run_notebook import Notebook


@navigator_parameterized(instance_name="small-instance")
def test_dask_gateway(navigator):
    input_output = [
        ("from dask_gateway import Gateway", ""),
        ("gateway = Gateway(); gateway", re.compile(r"Gateway*")),
        ("cluster = gateway.new_cluster(); cluster", re.compile(r"GatewayCluster")),
        ("client = cluster.get_client(); client", re.compile(r"Client")),
    ]

    test_app = Notebook(navigator=navigator)
    test_app.create_notebook(
        conda_env="conda-env-default-py"
    )

    for input, output in input_output:
        test_app.assert_code_output(input, output)
