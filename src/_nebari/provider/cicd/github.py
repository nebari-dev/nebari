import base64
import os
from typing import Dict, List, Optional, Union

import requests
from nacl import encoding, public
from pydantic import BaseModel, ConfigDict, Field, RootModel

from _nebari.constants import LATEST_SUPPORTED_PYTHON_VERSION
from _nebari.provider.cicd.common import pip_install_nebari
from nebari import schema

GITHUB_BASE_URL = "https://api.github.com/"


def github_request(url, method="GET", json=None, authenticate=True):
    auth = None
    if authenticate:
        missing = []
        for name in ("GITHUB_USERNAME", "GITHUB_TOKEN"):
            if os.environ.get(name) is None:
                missing.append(name)
        if len(missing) > 0:
            raise ValueError(
                f"Environment variable(s) required for GitHub automation - {', '.join(missing)}"
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


def gha_env_vars(config: schema.Main):
    env_vars = {
        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
    }

    if os.environ.get("NEBARI_GH_BRANCH"):
        env_vars["NEBARI_GH_BRANCH"] = "${{ secrets.NEBARI_GH_BRANCH }}"

    if config.provider == schema.ProviderEnum.aws:
        env_vars["AWS_ACCESS_KEY_ID"] = "${{ secrets.AWS_ACCESS_KEY_ID }}"
        env_vars["AWS_SECRET_ACCESS_KEY"] = "${{ secrets.AWS_SECRET_ACCESS_KEY }}"
        env_vars["AWS_DEFAULT_REGION"] = "${{ secrets.AWS_DEFAULT_REGION }}"
    elif config.provider == schema.ProviderEnum.azure:
        env_vars["ARM_CLIENT_ID"] = "${{ secrets.ARM_CLIENT_ID }}"
        env_vars["ARM_CLIENT_SECRET"] = "${{ secrets.ARM_CLIENT_SECRET }}"
        env_vars["ARM_SUBSCRIPTION_ID"] = "${{ secrets.ARM_SUBSCRIPTION_ID }}"
        env_vars["ARM_TENANT_ID"] = "${{ secrets.ARM_TENANT_ID }}"
    elif config.provider == schema.ProviderEnum.do:
        env_vars["AWS_ACCESS_KEY_ID"] = "${{ secrets.AWS_ACCESS_KEY_ID }}"
        env_vars["AWS_SECRET_ACCESS_KEY"] = "${{ secrets.AWS_SECRET_ACCESS_KEY }}"
        env_vars["SPACES_ACCESS_KEY_ID"] = "${{ secrets.SPACES_ACCESS_KEY_ID }}"
        env_vars["SPACES_SECRET_ACCESS_KEY"] = "${{ secrets.SPACES_SECRET_ACCESS_KEY }}"
        env_vars["DIGITALOCEAN_TOKEN"] = "${{ secrets.DIGITALOCEAN_TOKEN }}"
    elif config.provider == schema.ProviderEnum.gcp:
        env_vars["GOOGLE_CREDENTIALS"] = "${{ secrets.GOOGLE_CREDENTIALS }}"
        env_vars["PROJECT_ID"] = "${{ secrets.PROJECT_ID }}"
    elif config.provider in [schema.ProviderEnum.local, schema.ProviderEnum.existing]:
        # create mechanism to allow for extra env vars?
        pass
    else:
        raise ValueError("Cloud Provider configuration not supported")

    return env_vars


### GITHUB-ACTIONS SCHEMA ###


class GHA_on_extras(BaseModel):
    branches: List[str]
    paths: List[str]


GHA_on = RootModel[Dict[str, GHA_on_extras]]
GHA_job_steps_extras = RootModel[Union[str, float, int]]


class GHA_job_step(BaseModel):
    name: str
    uses: Optional[str] = None
    with_: Optional[Dict[str, GHA_job_steps_extras]] = Field(alias="with", default=None)
    run: Optional[str] = None
    env: Optional[Dict[str, GHA_job_steps_extras]] = None
    model_config = ConfigDict(populate_by_name=True)


class GHA_job_id(BaseModel):
    name: str
    runs_on_: str = Field(alias="runs-on")
    permissions: Optional[Dict[str, str]] = None
    steps: List[GHA_job_step]
    model_config = ConfigDict(populate_by_name=True)


GHA_jobs = RootModel[Dict[str, GHA_job_id]]


class GHA(BaseModel):
    name: str
    on: GHA_on
    env: Optional[Dict[str, str]] = None
    jobs: GHA_jobs


class NebariOps(GHA):
    pass


class NebariLinter(GHA):
    pass


### GITHUB ACTION WORKFLOWS ###


def checkout_image_step():
    return GHA_job_step(
        name="Checkout Image",
        uses="actions/checkout@v3",
        with_={"token": GHA_job_steps_extras("${{ secrets.REPOSITORY_ACCESS_TOKEN }}")},
    )


def setup_python_step():
    return GHA_job_step(
        name="Set up Python",
        uses="actions/setup-python@v4",
        with_={"python-version": GHA_job_steps_extras(LATEST_SUPPORTED_PYTHON_VERSION)},
    )


def install_nebari_step(nebari_version):
    return GHA_job_step(name="Install Nebari", run=pip_install_nebari(nebari_version))


def gen_nebari_ops(config):
    env_vars = gha_env_vars(config)

    push = GHA_on_extras(branches=[config.ci_cd.branch], paths=["nebari-config.yaml"])
    on = GHA_on({"push": push})

    step1 = checkout_image_step()
    step2 = setup_python_step()
    step3 = install_nebari_step(config.nebari_version)
    gha_steps = [step1, step2, step3]

    for step in config.ci_cd.before_script:
        gha_steps.append(GHA_job_step(**step))

    step4 = GHA_job_step(
        name="Deploy Changes made in nebari-config.yaml",
        run=f"nebari deploy -c nebari-config.yaml --disable-prompt{' --skip-remote-state-provision' if os.environ.get('NEBARI_GH_BRANCH') else ''}",
    )
    gha_steps.append(step4)

    step5 = GHA_job_step(
        name="Push Changes",
        run=(
            "git config user.email 'nebari@quansight.com' ; "
            "git config user.name 'github action' ; "
            "git add ./.gitignore ./.github ./stages; "
            "git diff --quiet && git diff --staged --quiet || (git commit -m '${{ env.COMMIT_MSG }}') ; "
            f"git push origin {config.ci_cd.branch}"
        ),
        env={
            "COMMIT_MSG": GHA_job_steps_extras(
                "nebari-config.yaml automated commit: ${{ github.sha }}"
            )
        },
    )
    if config.ci_cd.commit_render:
        gha_steps.append(step5)

    for step in config.ci_cd.after_script:
        gha_steps.append(GHA_job_step(**step))

    job1 = GHA_job_id(
        name="nebari",
        runs_on_="ubuntu-latest",
        permissions={
            "id-token": "write",
            "contents": "read",
        },
        steps=gha_steps,
    )
    jobs = GHA_jobs({"build": job1})

    return NebariOps(
        name="nebari auto update",
        on=on,
        env=env_vars,
        jobs=jobs,
    )


def gen_nebari_linter(config):
    env_vars = {}
    nebari_gh_branch = os.environ.get("NEBARI_GH_BRANCH")
    if nebari_gh_branch:
        env_vars["NEBARI_GH_BRANCH"] = "${{ secrets.NEBARI_GH_BRANCH }}"
    else:
        env_vars = None

    pull_request = GHA_on_extras(
        branches=[config.ci_cd.branch], paths=["nebari-config.yaml"]
    )
    on = GHA_on({"pull_request": pull_request})

    step1 = checkout_image_step()
    step2 = setup_python_step()
    step3 = install_nebari_step(config.nebari_version)

    step4_envs = {
        "PR_NUMBER": GHA_job_steps_extras("${{ github.event.number }}"),
        "REPO_NAME": GHA_job_steps_extras("${{ github.repository }}"),
        "GITHUB_TOKEN": GHA_job_steps_extras("${{ secrets.REPOSITORY_ACCESS_TOKEN }}"),
    }

    step4 = GHA_job_step(
        name="Nebari Lintify",
        run="nebari validate --config nebari-config.yaml --enable-commenting",
        env=step4_envs,
    )

    job1 = GHA_job_id(
        name="nebari", runs_on_="ubuntu-latest", steps=[step1, step2, step3, step4]
    )
    jobs = GHA_jobs(
        {
            "nebari-validate": job1,
        }
    )

    return NebariLinter(
        name="nebari linter",
        on=on,
        env=env_vars,
        jobs=jobs,
    )
