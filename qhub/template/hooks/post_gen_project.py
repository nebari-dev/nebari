import os
import shutil
import json
from ruamel import yaml

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
CLOUD_PROVIDER = "{{ cookiecutter.provider }}"
CLOUD_PROVIDERS = {'aws', 'do', 'gcp', 'azure'}
CI_PROVIDER = "{{ cookiecutter.ci_cd.type | default('none') }}"


# This Python file will be processed by Jinja2 so the below would show an error in your IDE if env_str was defined without triple quotes.
env_str = """
{{ cookiecutter.environments | jsonify | replace('"', '\\"') }}
"""
ENVIRONMENTS = json.loads(env_str)

TERRAFORM_STATE = "{{ cookiecutter.terraform_state.type }}"


def remove_directory(dirpath):
    shutil.rmtree(os.path.join(PROJECT_DIRECTORY, dirpath))


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    # render conda environments to directory "environments/*.yaml"
    if ENVIRONMENTS:
        os.makedirs("environments", exist_ok=True)
        for name, spec in ENVIRONMENTS.items():
            with open(f"environments/{name}", "w") as f:
                yaml.dump(spec, f, default_flow_style=False)

    # Remove any unused CI
    if CI_PROVIDER != "github-actions":
        remove_directory(".github")

    if CI_PROVIDER != "gitlab-ci":
        remove_file(".gitlab-ci.yml")

    # templates directory is only used by includes
    remove_directory("templates")
