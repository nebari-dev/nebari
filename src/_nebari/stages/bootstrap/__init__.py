from inspect import cleandoc
from typing import Any, Dict, List

from _nebari.provider.cicd.github import gen_nebari_linter, gen_nebari_ops
from _nebari.provider.cicd.gitlab import gen_gitlab_ci
from _nebari.utils import check_cloud_credentials
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


def gen_gitignore():
    """
    Generate `.gitignore` file.
    Add files as needed.
    """
    filestoignore = """
        # ignore terraform state
        .terraform
        terraform.tfstate
        terraform.tfstate.backup
        .terraform.tfstate.lock.info

        # python
        __pycache__
    """
    return {".gitignore": cleandoc(filestoignore)}


def gen_cicd(config):
    """
    Use cicd schema to generate workflow files based on the
    `ci_cd` key in the `config`.

    For more detail on schema:
    GiHub-Actions - nebari/providers/cicd/github.py
    GitLab-CI - nebari/providers/cicd/gitlab.py
    """
    cicd_files = {}

    if config.ci_cd.type == schema.CiEnum.github_actions:
        gha_dir = ".github/workflows/"
        cicd_files[gha_dir + "nebari-ops.yaml"] = gen_nebari_ops(config)
        cicd_files[gha_dir + "nebari-linter.yaml"] = gen_nebari_linter(config)

    elif config.ci_cd.type == schema.CiEnum.gitlab_ci:
        cicd_files[".gitlab-ci.yml"] = gen_gitlab_ci(config)

    else:
        raise ValueError(
            f"The ci_cd provider, {config.ci_cd.type.value}, is not supported. Supported providers include: `github-actions`, `gitlab-ci`."
        )

    return cicd_files


class BootstrapStage(NebariStage):
    name = "bootstrap"
    priority = 0

    def render(self) -> Dict[str, str]:
        contents = {}
        if self.config.ci_cd.type != schema.CiEnum.none:
            for fn, workflow in gen_cicd(self.config).items():
                workflow_json = workflow.json(
                    indent=2,
                    by_alias=True,
                    exclude_unset=True,
                    exclude_defaults=True,
                )
                workflow_yaml = yaml.dump(
                    json.loads(workflow_json), sort_keys=False, indent=2
                )
                contents.update({fn: workflow_yaml})

        contents.update(gen_gitignore())
        return contents

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
        check_cloud_credentials(self.config)


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [BootstrapStage]
