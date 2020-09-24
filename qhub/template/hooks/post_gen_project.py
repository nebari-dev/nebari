import os
import yaml
import subprocess

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROVIDER = "{{ cookiecutter.provider }}"
ENVIRONMENTS = eval("{{ cookiecutter.environments }}")
PATCHES = eval("{{ cookiecutter.patches }}")
RUN_DIRECTORY = "{{ cookiecutter.run_directory }}"


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    # Add environments to repository
    if ENVIRONMENTS:
        os.makedirs("environments", exist_ok=True)
        for name, spec in ENVIRONMENTS.items():
            with open(f"environments/{name}", "w") as f:
                yaml.dump(spec, f)

    # Remove terraform code for unused providers
    if PROVIDER == "aws":
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "do":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "gcp":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")

    # Last but not least apply patches
    # git apply <patch-name> generating patch files is in
    # documentation
    for patch_filename in PATCHES:
        absolute_patch_filename = (
            patch_filename
            if os.path.isabs(patch_filename)
            else os.path.join(RUN_DIRECTORY, patch_filename)
        )
        subprocess.check_output(["git", "apply", absolute_patch_filename])
