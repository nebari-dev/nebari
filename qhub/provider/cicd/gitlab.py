from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from qhub.constants import LATEST_SUPPORTED_PYTHON_VERSION
from qhub.provider.cicd.common import pip_install_qhub


class GLCI_extras(BaseModel):
    # to allow for dynamic key names
    __root__: Union[str, float, int]


class GLCI_image(BaseModel):
    name: str
    entrypoint: Optional[str]


class GLCI_rules(BaseModel):
    if_: Optional[str] = Field(alias="if")
    changes: Optional[List[str]]

    class Config:
        allow_population_by_field_name = True


class GLCI_job(BaseModel):
    image: Optional[Union[str, GLCI_image]]
    variables: Optional[Dict[str, str]]
    before_script: Optional[List[str]]
    after_script: Optional[List[str]]
    script: List[str]
    rules: Optional[List[GLCI_rules]]


class GLCI(BaseModel):
    __root__: Dict[str, GLCI_job]


def gen_gitlab_ci(config):

    branch = config["ci_cd"]["branch"]
    commit_render = config["ci_cd"].get("commit_render", True)
    before_script = config["ci_cd"].get("before_script")
    after_script = config["ci_cd"].get("after_script")
    pip_install = pip_install_qhub(config["qhub_version"])

    render_vars = {
        "COMMIT_MSG": "qhub-config.yaml automated commit: {{ '$CI_COMMIT_SHA' }}",
    }

    script = [
        f"git checkout {branch}",
        f"{pip_install}",
        "qhub deploy --config qhub-config.yaml --disable-prompt --skip-remote-state-provision",
    ]

    commit_render_script = [
        "git config user.email 'qhub@quansight.com'",
        "git config user.name 'gitlab ci'",
        "git add .",
        "git diff --quiet && git diff --staged --quiet || (git commit -m '${COMMIT_MSG}'",
        f"git push origin {branch})",
    ]

    if commit_render:
        script += commit_render_script

    rules = [
        GLCI_rules(
            if_=f"$CI_COMMIT_BRANCH == '{branch}'",
            changes=["qhub-config.yaml"],
        )
    ]

    render_qhub = GLCI_job(
        image=f"python:{LATEST_SUPPORTED_PYTHON_VERSION}",
        variables=render_vars,
        before_script=before_script,
        after_script=after_script,
        script=script,
        rules=rules,
    )

    return GLCI(
        __root__={
            "render-qhub": render_qhub,
        }
    )
