import pathlib
import collections
import json

from ruamel import yaml
from cookiecutter.main import cookiecutter
from cookiecutter.generate import generate_files
from ..version import __version__
from ..constants import TERRAFORM_VERSION


def patch_dask_gateway_extra_config(config):
    """Basically the current dask_gateway helm chart only allows one
    update to extraContainerConfig and extraPodConfig for the workers
    and scheduler. Thus we need to copy the configuration done in
    these settings. The only critical one is mounting the conda store
    directory.

    """
    conda_store_volume = {
        "name": "conda-store",
        "persistentVolumeClaim": {"claimName": "conda-store-dev-share"},
    }
    extra_pod_config = {"volumes": [conda_store_volume]}

    merge_config_for = ["worker_extra_pod_config", "scheduler_extra_pod_config"]

    if "profiles" in config and "dask_worker" in config["profiles"]:
        for worker_name, worker_config in config["profiles"]["dask_worker"].items():
            for config_name in merge_config_for:
                if config_name in worker_config:
                    worker_config[config_name] = deep_merge(
                        worker_config[config_name], extra_pod_config
                    )


def patch_versioning_extra_config(config):
    """
    Set defaults for qhub_version and terraform_modules
    because they depend on __version__ so cannot be static in cookiecutter.json
    """
    if "qhub_version" not in config:
        config["qhub_version"] = __version__

    if "terraform_modules" not in config:
        config["terraform_modules"] = {
            "repository": "github.com/quansight/qhub-terraform-modules",
            "rev": f"release-{__version__}",
        }

    if "terraform_version" not in config:
        config["terraform_version"] = TERRAFORM_VERSION


def deep_merge(d1, d2):
    """Deep merge two dictionaries.
    >>> value_1 = {
    'a': [1, 2],
    'b': {'c': 1, 'z': [5, 6]},
    'e': {'f': {'g': {}}},
    'm': 1,
    }

    >>> value_2 = {
        'a': [3, 4],
        'b': {'d': 2, 'z': [7]},
        'e': {'f': {'h': 1}},
        'm': [1],
    }

    >>> print(deep_merge(value_1, value_2))
    {'m': 1, 'e': {'f': {'g': {}, 'h': 1}}, 'b': {'d': 2, 'c': 1, 'z': [5, 6, 7]}, 'a': [1, 2, 3,  4]}
    """
    if isinstance(d1, dict) and isinstance(d2, dict):
        d3 = {}
        for key in d1.keys() | d2.keys():
            if key in d1 and key in d2:
                d3[key] = deep_merge(d1[key], d2[key])
            elif key in d1:
                d3[key] = d1[key]
            elif key in d2:
                d3[key] = d2[key]
        return d3
    elif isinstance(d1, list) and isinstance(d2, list):
        return [*d1, *d2]
    else:  # if they don't match use left one
        return d1


def render_default_template(output_directory, config_filename=None, force=False):
    import qhub

    input_directory = pathlib.Path(qhub.__file__).parent / "template"
    render_template(input_directory, output_directory, config_filename, force=force)


def render_template(
    input_directory, output_directory, config_filename=None, force=False
):
    # would be nice to remove assumption that input directory
    # is in local filesystem
    input_directory = pathlib.Path(input_directory)
    if not input_directory.is_dir():
        raise ValueError(f"input directory={input_directory} is not a directory")

    output_directory = pathlib.Path(output_directory).resolve()
    # due to cookiecutter requiring a template directory folder
    # we take the output directory and split into two components
    repo_directory = output_directory.name
    output_directory = output_directory.parent
    output_directory.mkdir(exist_ok=True, parents=True)

    prompt_filename = input_directory / "hooks" / "prompt_gen_project.py"

    if config_filename is not None:
        filename = pathlib.Path(config_filename)

        if not filename.is_file():
            raise ValueError(f"cookiecutter configuration={filename} is not filename")

        with filename.open() as f:
            config = yaml.safe_load(f)
            config["repo_directory"] = repo_directory
            patch_dask_gateway_extra_config(config)

        with (input_directory / "cookiecutter.json").open() as f:
            config = collections.ChainMap(config, json.load(f))

        patch_versioning_extra_config(config)

        generate_files(
            repo_dir=str(input_directory),
            context={"cookiecutter": config},
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
    elif prompt_filename.is_file():
        with prompt_filename.open() as f:
            content = f.read()

        global_context = {}
        exec(content, global_context, global_context)
        config = global_context["COOKIECUTTER_CONFIG"]

        patch_versioning_extra_config(config)

        cookiecutter(
            str(input_directory),
            no_input=True,
            extra_context=config,
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
    else:
        cookiecutter(
            str(input_directory),
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
