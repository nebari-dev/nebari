import os
import shutil

import yaml

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROVIDER = "{{ cookiecutter.provider }}"
CI_PROVIDER = "{{ cookiecutter.ci_cd }}"
ENVIRONMENTS = eval("{{ cookiecutter.environments }}")
TERRAFORM_STATE = "{{ cookiecutter.terraform_state.type }}"


def remove_directory(dirpath):
    shutil.rmtree(os.path.join(PROJECT_DIRECTORY, dirpath))


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    if ENVIRONMENTS:
        os.makedirs("environments", exist_ok=True)
        for name, spec in ENVIRONMENTS.items():
            with open(f"environments/{name}", "w") as f:
                yaml.dump(spec, f)

    # Managing provider terraform scripts
    if PROVIDER == "aws":
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
        remove_file("infrastructure/azure.tf")
    elif PROVIDER == "do":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/gcp.tf")
        remove_file("infrastructure/azure.tf")
    elif PROVIDER == "gcp":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/azure.tf")
    elif PROVIDER == "azure":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "local":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
        remove_file("infrastructure/azure.tf")

    # Managing terraform state scripts
    if TERRAFORM_STATE == "local":
        remove_directory("terraform-state")
        remove_file("infrastructure/state.tf")
    elif TERRAFORM_STATE == "existing":
        remove_directory("terraform-state")
    elif TERRAFORM_STATE == "remote" and PROVIDER == "local":
        remove_directory("terraform-state")

    # Managing ci/cd providers
    if CI_PROVIDER == "github-actions":
        remove_file(".gitlab-ci.yml")
    elif CI_PROVIDER == "gitlab-ci":
        remove_directory(".github")
    elif CI_PROVIDER == "none":
        remove_file(".gitlab-ci.yml")
        remove_directory(".github")

    # templates directory is only used by includes
    remove_directory("templates")
