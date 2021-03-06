import os
import base64

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
