import sys
import pathlib
import functools
import os
import shutil
from typing import List, Dict
import hashlib

from ruamel.yaml import YAML

from qhub.provider.terraform import tf_render_objects
from qhub.render.terraform import (
    QHubKubernetesProvider,
    QHubTerraformState,
    QHubGCPProvider,
    QHubAWSProvider,
)


def render_template(output_directory, config_filename, force=False, dry_run=False):
    # get directory for qhub templates
    import qhub

    template_directory = pathlib.Path(qhub.__file__).parent / "template"

    # would be nice to remove assumption that input directory
    # is in local filesystem and a directory
    template_directory = pathlib.Path(template_directory)
    if not template_directory.is_dir():
        raise ValueError(f"template directory={template_directory} is not a directory")

    output_directory = pathlib.Path(output_directory).resolve()

    if output_directory == str(pathlib.Path.home()):
        print("ERROR: Deploying QHub in home directory is not advised!")
        sys.exit(1)

    # mkdir all the way down to repo dir so we can copy .gitignore
    # into it in remove_existing_renders
    output_directory.mkdir(exist_ok=True, parents=True)

    config_filename = pathlib.Path(config_filename)
    if not config_filename.is_file():
        raise ValueError(
            f"cookiecutter configuration={config_filename} is not filename"
        )

    with config_filename.open() as f:
        yaml = YAML(typ="safe", pure=True)
        config = yaml.load(f)

    # For any config values that start with
    # QHUB_SECRET_, set the values using the
    # corresponding env var.
    set_env_vars_in_config(config)

    config["repo_directory"] = output_directory.name
    config["qhub_config_yaml_path"] = str(config_filename.absolute())

    contents = render_contents(config)

    directories = [
        "image",
        f"stages/02-infrastructure/{config['provider']}",
        "stages/03-kubernetes-initialize",
        "stages/04-kubernetes-ingress",
        "stages/05-kubernetes-keycloak",
        "stages/06-kubernetes-keycloak-configuration",
        "stages/07-kubernetes-services",
        "stages/08-enterprise-qhub",
    ]
    if config["provider"] != "local" and config["terraform_state"]["type"] == "remote":
        directories.append(f"stages/01-terraform-state/{config['provider']}")

    source_dirs = [os.path.join(str(template_directory), _) for _ in directories]
    output_dirs = [os.path.join(str(output_directory), _) for _ in directories]
    new, untrack, updated = inspect_files(
        source_dirs,
        output_dirs,
        source_base_dir=str(template_directory),
        output_base_dir=str(output_directory),
        ignore_filenames=[
            "terraform.tfstate",
            ".terraform.lock.hcl",
            "terraform.tfstate.backup",
        ],
        ignore_directories=[".terraform"],
        contents=contents,
    )

    if new:
        print("The following files will be created:")
        for filename in sorted(new):
            print(f"   CREATED   {filename}")
    if updated:
        print("The following files will be updated:")
        for filename in sorted(updated):
            print(f"   UPDATED   {filename}")
    if untrack:
        print("The following files are untracked (only exist in output directory):")
        for filename in sorted(updated):
            print(f"   UNTRACKED {filename}")

    if dry_run:
        print("dry-run enabled no files updated or created")
    else:
        for filename in new | updated:
            input_filename = os.path.join(str(template_directory), filename)
            output_filename = os.path.join(str(output_directory), filename)
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)

            if os.path.exists(input_filename):
                shutil.copyfile(input_filename, output_filename)
            else:
                with open(output_filename, "w") as f:
                    f.write(contents[filename])


def render_contents(config: Dict):
    """Dynamically generated contents from QHub configuration"""
    contents = {}

    if config["provider"] == "gcp":
        contents.update(
            {
                "stages/01-terraform-state/gcp/_qhub.tf.json": tf_render_objects(
                    [
                        QHubGCPProvider(config),
                    ]
                ),
                "stages/02-infrastructure/gcp/_qhub.tf.json": tf_render_objects(
                    [
                        QHubGCPProvider(config),
                        QHubTerraformState("02-infrastructure", config),
                    ]
                ),
            }
        )
    elif config["provider"] == "do":
        contents.update(
            {
                "stages/02-infrastructure/do/_qhub.tf.json": tf_render_objects(
                    [
                        QHubTerraformState("02-infrastructure", config),
                    ]
                )
            }
        )
    elif config["provider"] == "azure":
        contents.update(
            {
                "stages/02-infrastructure/azure/_qhub.tf.json": tf_render_objects(
                    [
                        QHubTerraformState("02-infrastructure", config),
                    ]
                )
            }
        )
    elif config["provider"] == "aws":
        contents.update(
            {
                "stages/01-terraform-state/aws/_qhub.tf.json": tf_render_objects(
                    [
                        QHubAWSProvider(config),
                    ]
                ),
                "stages/02-infrastructure/aws/_qhub.tf.json": tf_render_objects(
                    [
                        QHubAWSProvider(config),
                        QHubTerraformState("02-infrastructure", config),
                    ]
                ),
            }
        )

    contents.update(
        {
            "stages/03-kubernetes-initialize/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("03-kubernetes-initialize", config),
                    QHubKubernetesProvider(config),
                ]
            ),
            "stages/04-kubernetes-ingress/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("04-kubernetes-ingress", config),
                    QHubKubernetesProvider(config),
                ]
            ),
            "stages/05-kubernetes-keycloak/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("05-kubernetes-keycloak", config),
                    QHubKubernetesProvider(config),
                ]
            ),
            "stages/06-kubernetes-keycloak-configuration/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("06-kubernetes-keycloak-configuration", config),
                ]
            ),
            "stages/07-kubernetes-services/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("07-kubernetes-services", config),
                    QHubKubernetesProvider(config),
                ]
            ),
            "stages/08-enterprise-qhub/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("08-enterprise-qhub", config),
                    QHubKubernetesProvider(config),
                ]
            ),
        }
    )
    if config["ci_cd"]:
        for fn, data in gen_cicd(config).items():
            contents.update({fn: data.json(indent=2)})

    return contents


def gen_cicd(config):
    from .cicd import QhubOps

    cicd_files = {}

    env_vars = {
        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
    }

    if config["provider"] == "gcp":
        env_vars["GOOGLE_CREDENTIALS"] = "${{ secrets.GOOGLE_CREDENTIALS }}"
    # TODO: add envs for other cloud providers

    if config["ci_cd"]["type"] == "github-actions":
        # TODO: create similar schema/models for other GH action workflows
        qhubops = QhubOps(
            on=dict(
                push=dict(
                    branches=[config["ci_cd"]["branch"]], path=["qhub-config.yaml"]
                ),
            ),
            env=env_vars,
            jobs=dict(),
        )
        cicd_files["qhub_ops.yaml"] = qhubops

    elif config["ci_cd"]["type"] == "gitlab-ci":
        # TODO: create schema for GitLab-CI
        pass
    else:
        # should never get to this point... something has gone wrong
        pass

    return cicd_files


def inspect_files(
    source_dirs: str,
    output_dirs: str,
    source_base_dir: str,
    output_base_dir: str,
    ignore_filenames: List[str] = None,
    ignore_directories: List[str] = None,
    contents: Dict[str, str] = None,
):
    """Return created, updated and untracked files by computing a checksum over the provided directory

    Args:
        source_dirs (str): The source dir used as base for comparssion
        output_dirs (str): The destionation dir wich will be matched with
        source_base_dir (str): Relative base path to source directory
        output_base_dir (str): Relative base path to output directory
        ignore_filenames (list[str]): Filenames to ignore while comparing for changes
        ignore_directories (list[str]): Directories to ignore while comparing for changes
        contents (dict): filename to content mapping for dynmaically generated files
    """
    ignore_filenames = ignore_filenames or []
    ignore_directories = ignore_directories or []
    contents = contents or {}

    source_files = {}
    output_files = {}

    def list_files(
        directory: str, ignore_filenames: List[str], ignore_directories: List[str]
    ):
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_directories]
            for file in files:
                if file not in ignore_filenames:
                    yield os.path.join(root, file)

    for filename in contents:
        source_files[filename] = hashlib.sha256(
            contents[filename].encode("utf8")
        ).hexdigest()
        output_filename = os.path.join(output_base_dir, filename)
        if os.path.isfile(output_filename):
            output_files[filename] = hash_file(filename)

    for source_dir, output_dir in zip(source_dirs, output_dirs):
        for filename in list_files(source_dir, ignore_filenames, ignore_directories):
            relative_path = os.path.relpath(filename, source_base_dir)
            source_files[relative_path] = hash_file(filename)

        for filename in list_files(output_dir, ignore_filenames, ignore_directories):
            relative_path = os.path.relpath(filename, output_base_dir)
            output_files[relative_path] = hash_file(filename)

    new_files = source_files.keys() - output_files.keys()
    untracted_files = output_files.keys() - source_files.keys()
    updated_files = set()

    for prevalent_file in source_files.keys() & output_files.keys():
        if source_files[prevalent_file] != output_files[prevalent_file]:
            updated_files.add(prevalent_file)

    return new_files, untracted_files, updated_files


def hash_file(file_path: str):
    """Get the hex digest of the given file

    Args:
        file_path (str): path to file
    """
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def set_env_vars_in_config(config):
    """

    For values in the config starting with 'QHUB_SECRET_XXX' the environment
    variables are searched for the pattern XXX and the config value is
    modified. This enables setting secret values that should not be directly
    stored in the config file.

    NOTE: variables are most likely written to a file somewhere upon render. In
    order to further reduce risk of exposure of any of these variables you might
    consider preventing storage of the terraform render output.
    """
    private_entries = get_secret_config_entries(config)
    for idx in private_entries:
        set_qhub_secret(config, idx)


def get_secret_config_entries(config, config_idx=None, private_entries=None):
    output = private_entries or []
    if config_idx is None:
        sub_dict = config
        config_idx = []
    else:
        sub_dict = get_sub_config(config, config_idx)

    for key, value in sub_dict.items():
        if type(value) is dict:
            sub_dict_outputs = get_secret_config_entries(
                config, [*config_idx, key], private_entries
            )
            output = [*output, *sub_dict_outputs]
        else:
            if "QHUB_SECRET_" in str(value):
                output = [*output, [*config_idx, key]]
    return output


def get_sub_config(conf, conf_idx):
    sub_config = functools.reduce(dict.__getitem__, conf_idx, conf)
    return sub_config


def set_sub_config(conf, conf_idx, value):

    get_sub_config(conf, conf_idx[:-1])[conf_idx[-1]] = value


def set_qhub_secret(config, idx):
    placeholder = get_sub_config(config, idx)
    secret_var = get_qhub_secret(placeholder)
    set_sub_config(config, idx, secret_var)


def get_qhub_secret(secret_var):
    env_var = secret_var.lstrip("QHUB_SECRET_")
    val = os.environ.get(env_var)
    if not val:
        raise EnvironmentError(
            f"Since '{secret_var}' was found in the"
            " QHub config, the environment variable"
            f" '{env_var}' must be set."
        )
    return val
