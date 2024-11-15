DEPRECATED_FILE_PATHS = [
    # v0.4 removed in PR #1003 move to stages
    "infrastructure",
    "terraform-state",
    # v0.4 removed in PR #1068 deprecate some github actions
    ".github/workflows/image-pr.yaml",
    ".github/workflows/image.yaml",
    ".github/workflows/jupyterhub-pr.yaml",
    ".github/workflows/jupyterhub.yaml",
    # v2024.7.3 renamed misspelled file path
    "stages/07-kubernetes-services/modules/kubernetes/services/dask-gateway/controler.tf",  # codespell:ignore
]
