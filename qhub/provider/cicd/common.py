import os


def pip_install_qhub(qhub_version: str) -> str:
    qhub_gh_branch = os.environ.get("QHUB_GH_BRANCH", None)
    pip_install = f"pip install qhub=={qhub_version}"
    # dev branches
    if qhub_gh_branch:
        pip_install = (
            f"pip install git+https://github.com/Quansight/qhub.git@{qhub_gh_branch}"
        )

    return pip_install
