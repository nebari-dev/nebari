import os


def pip_install_nebari(nebari_version: str) -> str:
    nebari_gh_branch = os.environ.get("NEBARI_GH_BRANCH", None)
    pip_install = f"pip install nebari=={nebari_version}"
    # dev branches
    if nebari_gh_branch:
        pip_install = f"pip install git+https://github.com/nebari-dev/nebari.git@{nebari_gh_branch}"

    return pip_install
