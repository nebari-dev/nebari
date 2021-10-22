import tempfile
import os
import json

from qhub.provider import terraform
from qhub.constants import TERRAFORM_VERSION


def _write_terraform_test(directory):
    with open(os.path.join(directory, 'example.tf'), 'w') as f:
        f.write('''
resource "local_file" "main" {
    content     = "Hello, World!"
    filename    = "example.txt"
}

output "output_test" {
  description = "description of output"
  value = "test"
}
''')


def test_terraform_version():
    assert terraform.version() == TERRAFORM_VERSION

def test_terraform_init_apply_output_destroy():
    """Difficult to split into separate unit tests

    """
    with tempfile.TemporaryDirectory() as tempdir:
        _write_terraform_test(tempdir)
        terraform.init(tempdir)
        assert {'.terraform.lock.hcl', '.terraform', 'example.tf'} == set(os.listdir(tempdir))
        terraform.apply(tempdir)
        assert {'example.txt', 'terraform.tfstate', '.terraform.lock.hcl', '.terraform', 'example.tf'} == set(os.listdir(tempdir))
        output = json.loads(terraform.output(tempdir))
        assert output["output_test"]["value"] == "test"
        terraform.destroy(tempdir)
        assert {'terraform.tfstate.backup', 'terraform.tfstate', '.terraform.lock.hcl', '.terraform', 'example.tf'} == set(os.listdir(tempdir))
