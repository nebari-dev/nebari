import os
import base64

from typing import Optional, Dict, List, Union

from pydantic import BaseModel, Field

import requests
from nacl import encoding, public


def github_request(url, method="GET", json=None):
    GITHUB_BASE_URL = "https://api.github.com/"

    for name in ("GITHUB_USERNAME", "GITHUB_TOKEN"):
        if os.environ.get(name) is None:
            raise ValueError(
                f"environment variable={name} is required for github automation"
            )

    method_map = {
        "GET": requests.get,
        "PUT": requests.put,
        "POST": requests.post,
    }

    response = method_map[method](
        f"{GITHUB_BASE_URL}{url}",
        json=json,
        auth=requests.auth.HTTPBasicAuth(
            os.environ["GITHUB_USERNAME"], os.environ["GITHUB_TOKEN"]
        ),
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


### GITHUB-ACTIONS SCHEMA ###


class GHA_on_push(BaseModel):
    branches: List[str]
    path: List[str]


# TODO: make it dynamic
class GHA_on(BaseModel):
    push: GHA_on_push


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


class QhubOps(BaseModel):
    name: str = "qhub auto update"
    on: GHA_on
    env: Optional[Dict[str, str]]
    jobs: GHA_jobs


def gen_qhub_ops(config, env_vars):

    branch = config["ci_cd"]["branch"]

    on = GHA_on(push=GHA_on_push(branches=[branch], path=["qhub-config.yaml"]))

    step1 = GHA_job_step(
        name="Checkout Image",
        uses="actions/checkout@master",
        with_={
            "token": GHA_job_steps_extras(
                __root__="{{ '${{ secrets.REPOSITORY_ACCESS_TOKEN }}' }}"
            )
        },
    )

    step2 = GHA_job_step(
        name="Set up Python",
        uses="actions/setup-python@v2",
        with_={"python-version": GHA_job_steps_extras(__root__=3.8)},
    )

    step3 = GHA_job_step(
        name="Install QHub", run=f"pip install qhub=={config['qhub_version']}"
    )

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
            "git diff --quiet && git diff --staged --quiet || (git commit -m '${COMMIT_MSG}') ; "
            f"git push origin {branch}"
        ),
        env={
            "COMMIT_MSG": GHA_job_steps_extras(
                __root__="qhub-config.yaml automated commit: {{ '${{ github.sha }}' }}"
            )
        },
    )

    job1 = GHA_job_id(
        name="qhub", runs_on_="ubuntu-latest", steps=[step1, step2, step3, step4, step5]
    )
    jobs = GHA_jobs(__root__={"build": job1})

    return QhubOps(
        on=on,
        env=env_vars,
        jobs=jobs,
    )
