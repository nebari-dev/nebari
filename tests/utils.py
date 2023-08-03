from functools import partial

from _nebari.initialize import render_config

DEFAULT_TERRAFORM_STATE = "remote"

DEFAULT_GH_REPO = "github.com/test/test"
render_config_partial = partial(
    render_config,
    repository=DEFAULT_GH_REPO,
    repository_auto_provision=False,
    auth_auto_provision=False,
    terraform_state=DEFAULT_TERRAFORM_STATE,
    disable_prompt=True,
)
INIT_INPUTS = [
    # project, namespace, domain, cloud_provider, ci_provider, auth_provider
    ("pytestdo", "dev", "do.nebari.dev", "do", "github-actions", "github"),
    ("pytestaws", "dev", "aws.nebari.dev", "aws", "github-actions", "github"),
    ("pytestgcp", "dev", "gcp.nebari.dev", "gcp", "github-actions", "github"),
    ("pytestazure", "dev", "azure.nebari.dev", "azure", "github-actions", "github"),
]

NEBARI_CONFIG_FN = "nebari-config.yaml"
PRESERVED_DIR = "preserved_dir"
