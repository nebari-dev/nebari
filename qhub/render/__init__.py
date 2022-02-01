import pathlib
import functools
import os
from shutil import rmtree
import shutil
from turtle import up
from urllib.parse import urlencode

from ruamel.yaml import YAML
from ..version import __version__
from ..constants import TERRAFORM_VERSION
from ..utils import pip_install_qhub, QHUB_GH_BRANCH

# existing files and folders to delete when `render_template` is called
DELETABLE_PATHS = [
    "terraform-state",
    ".github",
    "infrastructure",
    "image",
    ".gitlab-ci.yml",
]


def patch_dask_gateway_extra_config(config):
    """Basically the current dask_gateway helm chart only allows one
    update to extraContainerConfig and extraPodConfig for the workers
    and scheduler. Thus we need to copy the configuration done in
    these settings. The only critical one is mounting the conda store
    directory.

    """
    namespace = config["namespace"]
    conda_store_volume = {
        "name": "conda-store",
        "persistentVolumeClaim": {"claimName": f"conda-store-{namespace}-share"},
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
    Set defaults for qhub_version and pip install command
    because they depend on __version__ so cannot be static in cookiecutter.json
    """
    if "qhub_version" not in config:
        config["qhub_version"] = __version__

    config["pip_install_qhub"] = pip_install_qhub

    config["QHUB_GH_BRANCH"] = QHUB_GH_BRANCH

    if "terraform_version" not in config:
        config["terraform_version"] = TERRAFORM_VERSION


def patch_terraform_extensions(config):
    """
    Add terraform-friendly extension details
    """
    config["tf_extensions"] = []
    logout_uris = []
    for ext in config.get("extensions", []):
        tf_ext = {
            "name": ext["name"],
            "image": ext["image"],
            "urlslug": ext["urlslug"],
            "private": ext.get("private", False),
            "oauth2client": ext.get("oauth2client", False),
            "logout": ext.get("logout", ""),
            "jwt": False,
            "qhubconfigyaml": ext.get("qhubconfigyaml", False),
        }
        tf_ext["envs"] = []
        for env in ext.get("envs", []):
            if env.get("code") == "KEYCLOAK":
                tf_ext["envs"].append(
                    {
                        "name": "KEYCLOAK_SERVER_URL",
                        "rawvalue": '"http://keycloak-headless.${var.environment}:8080/auth/"',
                    }
                )
                tf_ext["envs"].append(
                    {"name": "KEYCLOAK_ADMIN_USERNAME", "rawvalue": '"qhub-bot"'}
                )
                tf_ext["envs"].append(
                    {
                        "name": "KEYCLOAK_ADMIN_PASSWORD",
                        "rawvalue": "random_password.keycloak-qhub-bot-password.result",
                    }
                )
            elif env.get("code") == "OAUTH2CLIENT":
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_AUTHORIZE_URL",
                        "rawvalue": '"https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/auth"',
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_ACCESS_TOKEN_URL",
                        "rawvalue": '"https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/token"',
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_USER_DATA_URL",
                        "rawvalue": '"https://${var.endpoint}/auth/realms/qhub/protocol/openid-connect/userinfo"',
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_CLIENT_ID",
                        "rawvalue": f"\"qhub-ext-{ext['name']}-client\"",
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_CLIENT_SECRET",
                        "rawvalue": f"random_password.qhub-ext-{ext['name']}-keycloak-client-pw.result",
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "OAUTH2_REDIRECT_BASE",
                        "rawvalue": f"\"https://${{var.endpoint}}/{ext['urlslug']}/\"",
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "COOKIE_OAUTH2STATE_NAME",
                        "rawvalue": f"\"qhub-o2state-{ext['name']}\"",
                    }
                )
            elif env.get("code") == "JWT":
                tf_ext["envs"].append(
                    {
                        "name": "JWT_SECRET_KEY",
                        "rawvalue": f"random_password.qhub-ext-{ext['name']}-jwt-secret.result",
                    }
                )
                tf_ext["envs"].append(
                    {
                        "name": "COOKIE_AUTHORIZATION_NAME",
                        "rawvalue": f"\"qhub-jwt-{ext['name']}\"",
                    }
                )
                tf_ext["jwt"] = True
            else:
                raise ValueError("No such QHub extension code " + env.get("code"))

        if ext.get("logout", "") != "":
            logout_uris.append(
                f"https://{config['domain']}/{ext['urlslug']}{ext['logout']}"
            )

        config["tf_extensions"].append(tf_ext)

    final_logout_uri = f"https://{config['domain']}/hub/login"

    for uri in logout_uris:
        final_logout_uri = "{}?{}".format(
            uri, urlencode({"redirect_uri": final_logout_uri})
        )

    config["final_logout_uri"] = final_logout_uri
    config["logout_uris"] = logout_uris


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


def render_template(output_directory, config_filename, force=False):
    import qhub

    input_directory = pathlib.Path(qhub.__file__).parent / "template"

    # would be nice to remove assumption that input directory
    # is in local filesystem
    input_directory = pathlib.Path(input_directory)
    if not input_directory.is_dir():
        raise ValueError(f"input directory={input_directory} is not a directory")

    output_directory = pathlib.Path(output_directory).resolve()
    #
    from pathlib import Path

    if output_directory == str(Path.home()):
        print("Deploying on /home is not advised!")
        return

    # mkdir all the way down to repo dir so we can copy .gitignore into it in remove_existing_renders
    output_directory.mkdir(exist_ok=True, parents=True)

    filename = pathlib.Path(config_filename)

    if not filename.is_file():
        raise ValueError(f"cookiecutter configuration={filename} is not filename")

    with filename.open() as f:
        yaml = YAML(typ="safe", pure=True)
        config = yaml.load(f)

    # For any config values that start with
    # QHUB_SECRET_, set the values using the
    # corresponding env var.
    set_env_vars_in_config(config)

    config["repo_directory"] = output_directory.name
    patch_dask_gateway_extra_config(config)

    patch_versioning_extra_config(config)

    patch_terraform_extensions(config)

    config["qhub_config_yaml_path"] = str(filename.absolute())

    directories = ["stages", "image"]

    source_dirs = [os.path.join(str(input_directory), _) for _ in directories]
    output_dirs = [os.path.join(str(output_directory), _) for _ in directories]
    new, untrack, updated = inspect_files(
        source_dirs,
        output_dirs,
        source_base_dir=str(input_directory),
        output_base_dir=str(output_directory),
    )
    track_list = {"CREATED": new, "MODIFIED": untrack, "UNTRACKED": updated}
    for mode in track_list.keys():
        if mode != "UNTRACKED":
            print(f"The following files will be {mode.lower()}...")
        else:
            print("The following files are untracked...")
        for file in sorted(track_list[mode]):
            print(f"   {mode} {file}")

    for filename in new | updated:
        output_filename = os.path.join(str(output_directory), filename)
        input_filename = os.path.join(str(input_directory), filename)
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        shutil.copyfile(input_filename, output_filename)


def inspect_files(
    source_dirs: str, output_dirs: str, source_base_dir: str, output_base_dir: str
):
    """Return created, updated and untracked files by computing a checksum over the provided directory

    Args:
        source_dirs (str): The source dir used as base for comparssion
        output_dirs (str): The destionation dir wich will be matched with
        source_base_dir (str): Relative base path to source directory
        output_base_dir (str): Relative base path to output directory
    """

    source_files = {}
    output_files = {}

    for source_dir, output_dir in zip(source_dirs, output_dirs):

        for root, _, files in os.walk(source_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                source_files[os.path.relpath(file_path, source_base_dir)] = hash_file(
                    file_path
                )

        for root, _, files in os.walk(output_dir):
            for file_name in files:
                outfile_path = os.path.join(root, file_name)
                output_files[
                    os.path.relpath(outfile_path, output_base_dir)
                ] = hash_file(outfile_path)

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
    import hashlib

    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def remove_existing_renders(
    output_directory, deletable_paths=DELETABLE_PATHS, verbosity=0
):
    """
    Remove all files and directories beneath each directory in `deletable_paths`. These files and directories will be regenerated in the next step (`generate_files`) based on the configurations set in `qhub-config.yml`.

    Inputs must be pathlib.Path
    """
    home_dir = pathlib.Path.home()
    if pathlib.Path.cwd() == home_dir:
        raise ValueError(
            f"Deploying QHub from the home directory, {home_dir}, is not permitted."
        )

    for delete_me in deletable_paths:
        delete_me = dest_repo_dir / delete_me
        if delete_me.exists():
            if verbosity > 0:
                print(f"Deleting all files and directories beneath {delete_me} ...")
            if delete_me.is_file():
                delete_me.unlink()
            else:
                rmtree(delete_me)


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
