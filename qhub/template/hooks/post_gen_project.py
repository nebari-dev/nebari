import os
import shutil

from ruamel import yaml

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROVIDER = "{{ cookiecutter.provider }}"
CI_PROVIDER = "{{ cookiecutter.ci_cd.type | default('none') }}"
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

    # Remove any unused cloud infrastructure
    if PROVIDER != "aws":
        remove_file("infrastructure/aws.tf")
        remove_directory("infrastructure/modules/aws")

    if PROVIDER != "do":
        remove_file("infrastructure/do.tf")
        remove_directory("infrastructure/modules/digitalocean")

    if PROVIDER != "gcp":
        remove_file("infrastructure/gcp.tf")
        remove_directory("infrastructure/modules/gcp")

    if PROVIDER != "azure":
        remove_file("infrastructure/azure.tf")
        remove_directory("infrastructure/modules/azure")

    # if PROVIDER == "local" all above will have been removed

    # Remove any unused state

    if TERRAFORM_STATE == "local":
        remove_file("infrastructure/state.tf")

    if TERRAFORM_STATE != "remote" or PROVIDER == "local":
        remove_directory("terraform-state")
    else:
        # Remove the clouds we don't need:
        if PROVIDER != "aws":
            remove_directory("terraform-state/modules/aws")

        if PROVIDER != "do":
            remove_directory("terraform-state/modules/digitalocean")

        if PROVIDER != "gcp":
            remove_directory("terraform-state/modules/gcp")

        if PROVIDER != "azure":
            remove_directory("terraform-state/modules/azure")

    # Remove any unused CI

    if CI_PROVIDER != "github-actions":
        remove_directory(".github")

    if CI_PROVIDER != "gitlab-ci":
        remove_file(".gitlab-ci.yml")

    # if CI_PROVIDER == "none" all above will have been removed

    # templates directory is only used by includes
    remove_directory("templates")
