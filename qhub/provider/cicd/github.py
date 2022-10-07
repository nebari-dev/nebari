import base64
import os
import re
from typing import Dict, List, Optional, Union

import requests
from nacl import encoding, public
from pydantic import BaseModel, Field

from qhub.constants import LATEST_SUPPORTED_PYTHON_VERSION
from qhub.provider.cicd.common import pip_install_qhub

GITHUB_BASE_URL = "https://api.github.com/"


def github_request(url, method="GET", json=None, authenticate=True):
    auth = None
    if authenticate:
        for name in ("GITHUB_USERNAME", "GITHUB_TOKEN"):
            if os.environ.get(name) is None:
                raise ValueError(
                    f"Environment variable={name} is required for GitHub automation"
                )
        auth = requests.auth.HTTPBasicAuth(
            os.environ["GITHUB_USERNAME"], os.environ["GITHUB_TOKEN"]
        )

    method_map = {
        "GET": requests.get,
        "PUT": requests.put,
        "POST": requests.post,
    }

    response = method_map[method](
        f"{GITHUB_BASE_URL}{url}",
        json=json,
        auth=auth,
    )
    response.raise_for_status()
    return response


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def get_repo_public_key(owner, repo):
    return github_request(f"repos/{owner}/{repo}/actions/secrets/public-key").json()


def update_secret(owner, repo, secret_name, secret_value):
    key = get_repo_public_key(owner, repo)
    encrypted_value = encrypt(key["key"], secret_value)

    return github_request(
        f"repos/{owner}/{repo}/actions/secrets/{secret_name}",
        method="PUT",
        json={"encrypted_value": encrypted_value, "key_id": key["key_id"]},
    )


def get_repository(owner, repo):
    return github_request(f"repos/{owner}/{repo}").json()


def get_repo_tags(owner, repo):
    return github_request(f"repos/{owner}/{repo}/tags", authenticate=False).json()


def get_latest_repo_tag(owner: str, repo: str, only_clean_tags: bool = True) -> str:
    """
    Get the latest available tag on GitHub for owner/repo.

    NOTE: Set `only_clean_tags=False` to include dev / pre-release (if latest).
    """
    tags = get_repo_tags(owner, repo)
    if not only_clean_tags and len(tags) >= 1:
        return tags[0].get("name")
    for t in tags:
        rel = list(filter(None, re.sub(r"[A-Za-z]", " ", t["name"]).split(" ")))
        if len(rel) == 1:
            return t.get("name")


def create_repository(owner, repo, description, homepage, private=True):
    if owner == os.environ.get("GITHUB_USERNAME"):
        github_request(
            "user/repos",
            method="POST",
            json={
                "name": repo,
                "description": description,
                "homepage": homepage,
                "private": private,
            },
        )
    else:
        github_request(
            f"orgs/{owner}/repos",
            method="POST",
            json={
                "name": repo,
                "description": description,
                "homepage": homepage,
                "private": private,
            },
        )
    return f"git@github.com:{owner}/{repo}.git"


def gha_env_vars(config):
    env_vars = {
        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
    }

    if os.environ.get("QHUB_GH_BRANCH"):
        env_vars["QHUB_GH_BRANCH"] = "${{ secrets.QHUB_GH_BRANCH }}"

    # This assumes that the user is using the omitting sensitive values configuration for the token.
    if config.get("prefect", {}).get("enabled", False):
        env_vars[
            "QHUB_SECRET_prefect_token"
        ] = "${{ secrets.QHUB_SECRET_PREFECT_TOKEN }}"

    if config["provider"] == "aws":
        env_vars["AWS_ACCESS_KEY_ID"] = "${{ secrets.AWS_ACCESS_KEY_ID }}"
        env_vars["AWS_SECRET_ACCESS_KEY"] = "${{ secrets.AWS_SECRET_ACCESS_KEY }}"
        env_vars["AWS_DEFAULT_REGION"] = "${{ secrets.AWS_DEFAULT_REGION }}"
    elif config["provider"] == "azure":
        env_vars["ARM_CLIENT_ID"] = "${{ secrets.ARM_CLIENT_ID }}"
        env_vars["ARM_CLIENT_SECRET"] = "${{ secrets.ARM_CLIENT_SECRET }}"
        env_vars["ARM_SUBSCRIPTION_ID"] = "${{ secrets.ARM_SUBSCRIPTION_ID }}"
        env_vars["ARM_TENANT_ID"] = "${{ secrets.ARM_TENANT_ID }}"
    elif config["provider"] == "do":
        env_vars["AWS_ACCESS_KEY_ID"] = "${{ secrets.AWS_ACCESS_KEY_ID }}"
        env_vars["AWS_SECRET_ACCESS_KEY"] = "${{ secrets.AWS_SECRET_ACCESS_KEY }}"
        env_vars["SPACES_ACCESS_KEY_ID"] = "${{ secrets.SPACES_ACCESS_KEY_ID }}"
        env_vars["SPACES_SECRET_ACCESS_KEY"] = "${{ secrets.SPACES_SECRET_ACCESS_KEY }}"
        env_vars["DIGITALOCEAN_TOKEN"] = "${{ secrets.DIGITALOCEAN_TOKEN }}"
    elif config["provider"] == "gcp":
        env_vars["GOOGLE_CREDENTIALS"] = "${{ secrets.GOOGLE_CREDENTIALS }}"
    elif config["provider"] in ["local", "existing"]:
        # create mechanism to allow for extra env vars?
        pass
    else:
        raise ValueError("Cloud Provider configuration not supported")

    return env_vars


### GITHUB-ACTIONS SCHEMA ###


class GHA_on_extras(BaseModel):
    branches: List[str]
    paths: List[str]


class GHA_on(BaseModel):
    # to allow for dynamic key names
    __root__: Dict[str, GHA_on_extras]

    # TODO: validate __root__ values
    # `push`, `pull_request`, etc.


class GHA_job_steps_extras(BaseModel):
    # to allow for dynamic key names
    __root__: Union[str, float, int]


class GHA_job_step(BaseModel):
    name: str
    uses: Optional[str]
    with_: Optional[Dict[str, GHA_job_steps_extras]] = Field(alias="with")
    run: Optional[str]
    env: Optional[Dict[str, GHA_job_steps_extras]]

    class Config:
        allow_population_by_field_name = True


class GHA_job_id(BaseModel):
    name: str
    runs_on_: str = Field(alias="runs-on")
    steps: List[GHA_job_step]

    class Config:
        allow_population_by_field_name = True


class GHA_jobs(BaseModel):
    # to allow for dynamic key names
    __root__: Dict[str, GHA_job_id]


class GHA(BaseModel):
    name: str
    on: GHA_on
    env: Optional[Dict[str, str]]
    jobs: GHA_jobs


class QhubOps(GHA):
    pass


class QhubLinter(GHA):
    pass


### GITHUB ACTION WORKFLOWS ###


def checkout_image_step():
    return GHA_job_step(
        name="Checkout Image",
        uses="actions/checkout@master",
        with_={
            "token": GHA_job_steps_extras(
                __root__="${{ secrets.REPOSITORY_ACCESS_TOKEN }}"
            )
        },
    )


def setup_python_step():
    return GHA_job_step(
        name="Set up Python",
        uses="actions/setup-python@v2",
        with_={
            "python-version": GHA_job_steps_extras(
                __root__=LATEST_SUPPORTED_PYTHON_VERSION
            )
        },
    )


def install_qhub_step(qhub_version):
    return GHA_job_step(name="Install QHub", run=pip_install_qhub(qhub_version))


def gen_qhub_ops(config):

    env_vars = gha_env_vars(config)
    branch = config["ci_cd"]["branch"]
    commit_render = config["ci_cd"].get("commit_render", True)
    qhub_version = config["qhub_version"]

    push = GHA_on_extras(branches=[branch], paths=["qhub-config.yaml"])
    on = GHA_on(__root__={"push": push})

    step1 = checkout_image_step()
    step2 = setup_python_step()
    step3 = install_qhub_step(qhub_version)

    step4 = GHA_job_step(
        name="Deploy Changes made in qhub-config.yaml",
        run=f"qhub deploy -c qhub-config.yaml --disable-prompt{' --skip-remote-state-provision' if os.environ.get('QHUB_GH_BRANCH') else ''}",
    )

    step5 = GHA_job_step(
        name="Push Changes",
        run=(
            "git config user.email 'qhub@quansight.com' ; "
            "git config user.name 'github action' ; "
            "git add . ; "
            "git diff --quiet && git diff --staged --quiet || (git commit -m '${{ env.COMMIT_MSG }}') ; "
            f"git push origin {branch}"
        ),
        env={
            "COMMIT_MSG": GHA_job_steps_extras(
                __root__="qhub-config.yaml automated commit: ${{ github.sha }}"
            )
        },
    )

    gha_steps = [step1, step2, step3, step4]
    if commit_render:
        gha_steps.append(step5)

    job1 = GHA_job_id(name="qhub", runs_on_="ubuntu-latest", steps=gha_steps)
    jobs = GHA_jobs(__root__={"build": job1})

    return QhubOps(
        name="qhub auto update",
        on=on,
        env=env_vars,
        jobs=jobs,
    )


def gen_qhub_linter(config):

    env_vars = {}
    qhub_gh_branch = os.environ.get("QHUB_GH_BRANCH")
    if qhub_gh_branch:
        env_vars["QHUB_GH_BRANCH"] = "${{ secrets.QHUB_GH_BRANCH }}"
    else:
        env_vars = None

    branch = config["ci_cd"]["branch"]
    qhub_version = config["qhub_version"]

    pull_request = GHA_on_extras(branches=[branch], paths=["qhub-config.yaml"])
    on = GHA_on(__root__={"pull_request": pull_request})

    step1 = checkout_image_step()
    step2 = setup_python_step()
    step3 = install_qhub_step(qhub_version)

    step4_envs = {
        "PR_NUMBER": GHA_job_steps_extras(__root__="${{ github.event.number }}"),
        "REPO_NAME": GHA_job_steps_extras(__root__="${{ github.repository }}"),
        "GITHUB_TOKEN": GHA_job_steps_extras(
            __root__="${{ secrets.REPOSITORY_ACCESS_TOKEN }}"
        ),
    }

    step4 = GHA_job_step(
        name="QHub Lintify",
        run="qhub validate --config qhub-config.yaml --enable-commenting",
        env=step4_envs,
    )

    job1 = GHA_job_id(
        name="qhub", runs_on_="ubuntu-latest", steps=[step1, step2, step3, step4]
    )
    jobs = GHA_jobs(
        __root__={
            "qhub-validate": job1,
        }
    )

    return QhubLinter(
        name="qhub linter",
        on=on,
        env=env_vars,
        jobs=jobs,
    )
