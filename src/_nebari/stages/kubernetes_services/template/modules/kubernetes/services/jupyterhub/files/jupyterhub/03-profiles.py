import ast
import copy
import functools
import json
from pathlib import Path

import z2jh
from tornado import gen


def base_profile_home_mounts(username):
    """Configure the home directory mount for user.

    Ensure that user directory exists and user has permissions to
    read/write/execute.

    """
    home_pvc_name = z2jh.get_config("custom.home-pvc")
    skel_mount = z2jh.get_config("custom.skel-mount")
    pvc_home_mount_path = "home/{username}"
    pod_home_mount_path = "/home/{username}"

    extra_pod_config = {
        "volumes": [
            {
                "name": "home",
                "persistentVolumeClaim": {
                    "claimName": home_pvc_name,
                },
            },
            {
                "name": "skel",
                "configMap": {
                    "name": skel_mount["name"],
                },
            },
        ]
    }

    extra_container_config = {
        "volumeMounts": [
            {
                "mountPath": pod_home_mount_path.format(username=username),
                "name": "home",
                "subPath": pvc_home_mount_path.format(username=username),
            },
        ]
    }

    MKDIR_OWN_DIRECTORY = (
        "mkdir -p /mnt/{path} && chmod 777 /mnt/{path} && "
        # Copy skel files/folders not starting with '..' to user home directory.
        # Filtering out ..* removes some unneeded folders (k8s configmap mount implementation details).
        "find /etc/skel/. -maxdepth 1 -not -name '.' -not -name '..*' -exec "
        "cp -rL {escaped_brackets} /mnt/{path} \;"
    )
    command = MKDIR_OWN_DIRECTORY.format(
        # have to escape the brackets since this string will be formatted later by KubeSpawner
        escaped_brackets="{{}}",
        path=pvc_home_mount_path.format(username=username),
    )
    init_containers = [
        {
            "name": "initialize-home-mount",
            "image": "busybox:1.31",
            "command": ["sh", "-c", command],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [
                {
                    "mountPath": f"/mnt/{pvc_home_mount_path.format(username=username)}",
                    "name": "home",
                    "subPath": pvc_home_mount_path.format(username=username),
                },
                {"mountPath": "/etc/skel", "name": "skel"},
            ],
        }
    ]
    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
        "init_containers": init_containers,
    }


def base_profile_shared_mounts(groups_to_volume_mount):
    """Configure the group directory mounts for user.

    Ensure that {shared}/{group} directory exists based on the scope availability
    and if user has permissions to read/write/execute. Kubernetes does not allow the
    same pvc to be a volume thus we must check that the home and share
    pvc are not the same for some operation.

    """
    home_pvc_name = z2jh.get_config("custom.home-pvc")
    shared_pvc_name = z2jh.get_config("custom.shared-pvc")

    pvc_shared_mount_path = "shared/{group}"
    pod_shared_mount_path = "/shared/{group}"

    extra_pod_config = {"volumes": []}
    if home_pvc_name != shared_pvc_name:
        extra_pod_config["volumes"].append(
            {"name": "shared", "persistentVolumeClaim": {"claimName": shared_pvc_name}}
        )

    extra_container_config = {"volumeMounts": []}

    MKDIR_OWN_DIRECTORY = "mkdir -p /mnt/{path} && chmod 777 /mnt/{path}"
    command = " && ".join(
        [
            MKDIR_OWN_DIRECTORY.format(path=pvc_shared_mount_path.format(group=group))
            for group in groups_to_volume_mount
        ]
    )

    init_containers = [
        {
            "name": "initialize-shared-mounts",
            "image": "busybox:1.31",
            "command": ["sh", "-c", command],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [],
        }
    ]

    for group in groups_to_volume_mount:
        extra_container_config["volumeMounts"].append(
            {
                "mountPath": pod_shared_mount_path.format(group=group),
                "name": "shared" if home_pvc_name != shared_pvc_name else "home",
                "subPath": pvc_shared_mount_path.format(group=group),
            }
        )
        init_containers[0]["volumeMounts"].append(
            {
                "mountPath": f"/mnt/{pvc_shared_mount_path.format(group=group)}",
                "name": "shared" if home_pvc_name != shared_pvc_name else "home",
                "subPath": pvc_shared_mount_path.format(group=group),
            }
        )

    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
        "init_containers": init_containers,
    }


def profile_conda_store_mounts(username, groups):
    """Configure the conda_store environment directories mounts for
    user.

    Ensure that {shared}/{group} directory exists and user has
    permissions to read/write/execute.

    """
    conda_store_pvc_name = z2jh.get_config("custom.conda-store-pvc")
    conda_store_mount = Path(z2jh.get_config("custom.conda-store-mount"))
    default_namespace = z2jh.get_config("custom.default-conda-store-namespace")

    extra_pod_config = {
        "volumes": [
            {
                "name": "conda-store",
                "persistentVolumeClaim": {
                    "claimName": conda_store_pvc_name,
                },
            }
        ]
    }

    conda_store_namespaces = [username, default_namespace, "global"] + groups
    extra_container_config = {
        "volumeMounts": [
            {
                "mountPath": str(conda_store_mount / namespace),
                "name": "conda-store",
                "subPath": namespace,
            }
            for namespace in conda_store_namespaces
        ]
    }

    MKDIR_OWN_DIRECTORY = "mkdir -p /mnt/{path} && chmod 755 /mnt/{path}"
    command = " && ".join(
        [
            MKDIR_OWN_DIRECTORY.format(path=namespace)
            for namespace in conda_store_namespaces
        ]
    )
    init_containers = [
        {
            "name": "initialize-conda-store-mounts",
            "image": "busybox:1.31",
            "command": ["sh", "-c", command],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [
                {
                    "mountPath": f"/mnt/{namespace}",
                    "name": "conda-store",
                    "subPath": namespace,
                }
                for namespace in conda_store_namespaces
            ],
        }
    ]
    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
        "init_containers": init_containers,
    }


def base_profile_extra_mounts():
    extra_mounts = z2jh.get_config("custom.extra-mounts")

    extra_pod_config = {
        "volumes": [
            (
                {
                    "name": volume["name"],
                    "persistentVolumeClaim": {"claimName": volume["name"]},
                }
                if volume["kind"] == "persistentvolumeclaim"
                else {"name": volume["name"], "configMap": {"name": volume["name"]}}
            )
            for mount_path, volume in extra_mounts.items()
        ]
    }

    extra_container_config = {
        "volumeMounts": [
            {
                "name": volume["name"],
                "mountPath": mount_path,
            }
            for mount_path, volume in extra_mounts.items()
        ]
    }
    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
    }


def configure_user_provisioned_repositories(username):
    # Define paths and configurations
    pvc_home_mount_path = f"home/{username}"

    git_repos_provision_pvc = z2jh.get_config("custom.initial-repositories")
    git_clone_update_config = {
        "name": "git-clone-update",
        "configMap": {"name": "git-clone-update", "defaultMode": 511},
    }

    # Convert the string configuration to a list of dictionaries
    def string_to_objects(input_string):
        try:
            result = ast.literal_eval(input_string)
            if isinstance(result, list) and all(
                isinstance(item, dict) for item in result
            ):
                return result
            else:
                raise ValueError(
                    "Input string does not contain a list of dictionaries."
                )
        except (ValueError, SyntaxError):
            # Return an error message if the input string is not a list of dictionaries
            raise ValueError(f"Invalid input string format: {input_string}")

    git_repos_provision_pvc = string_to_objects(git_repos_provision_pvc)

    if not git_repos_provision_pvc:
        return {}

    # Define the extra pod configuration for the volumes
    extra_pod_config = {
        "volumes": [{"name": "git-clone-update", **git_clone_update_config}]
    }

    extras_git_clone_cp_path = f"/mnt/{pvc_home_mount_path}/.git-clone-update.sh"

    BASH_EXECUTION = "./.git-clone-update.sh"

    for local_repo_pair in git_repos_provision_pvc:
        for path, remote_url in local_repo_pair.items():
            BASH_EXECUTION += f" '{path} {remote_url}'"

    EXEC_OWNERSHIP_CHANGE = " && ".join(
        [
            f"cp /mnt/extras/git-clone-update.sh {extras_git_clone_cp_path}",
            f"chmod 777 {extras_git_clone_cp_path}",
            f"chown -R 1000:100 {extras_git_clone_cp_path}",
            f"cd /mnt/{pvc_home_mount_path}",
            BASH_EXECUTION,
            f"rm -f {extras_git_clone_cp_path}",
        ]
    )

    # Define init containers configuration
    init_containers = [
        {
            "name": "pre-populate-git-repos",
            "image": "bitnami/git",
            "command": ["sh", "-c", EXEC_OWNERSHIP_CHANGE],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [
                {
                    "mountPath": f"/mnt/{pvc_home_mount_path}",
                    "name": "home",
                    "subPath": pvc_home_mount_path,
                },
                {"mountPath": "/mnt/extras", "name": "git-clone-update"},
            ],
        }
    ]

    return {
        "extra_pod_config": extra_pod_config,
        "init_containers": init_containers,
    }


def configure_user(username, groups, uid=1000, gid=100):
    environment = {
        # nss_wrapper
        # https://cwrap.org/nss_wrapper.html
        "LD_PRELOAD": "libnss_wrapper.so",
        "NSS_WRAPPER_PASSWD": "/tmp/passwd",
        "NSS_WRAPPER_GROUP": "/tmp/group",
        # default files created will have 775 permissions
        "NB_UMASK": "0002",
        # set default shell to bash
        "SHELL": "/bin/bash",
        # set home directory to username
        "HOME": f"/home/{username}",
        # Disable global usage of pip
        "PIP_REQUIRE_VIRTUALENV": "true",
    }

    etc_passwd, etc_group = generate_nss_files(
        users=[{"username": username, "uid": uid, "gid": gid}],
        groups=[{"groupname": "users", "gid": gid}],
    )

    jupyter_config = json.dumps(
        {
            # nb_conda_kernels configuration
            # https://github.com/Anaconda-Platform/nb_conda_kernels
            "CondaKernelSpecManager": {"name_format": "{environment}"}
        }
    )

    # condarc to add all the namespaces user has access to
    default_namespace = z2jh.get_config("custom.default-conda-store-namespace")
    condarc = json.dumps(
        {
            "envs_dirs": [
                f"/home/conda/{_}/envs"
                for _ in [
                    username,
                    default_namespace,
                    "global",
                ]
                + groups
            ]
        }
    )

    command = " && ".join(
        [
            # nss_wrapper
            # https://cwrap.org/nss_wrapper.html
            f"echo '{etc_passwd}' > /tmp/passwd",
            f"echo '{etc_group}' > /tmp/group",
            # mount the shared directories for user only if there are
            # shared folders (groups) that the user is a member of
            # else ensure that the `shared` folder symlink does not exist
            (
                f"ln -sfn /shared /home/{username}/shared"
                if groups
                else f"rm -f /home/{username}/shared"
            ),
            # conda-store environment configuration
            f"printf '{condarc}' > /home/{username}/.condarc",
            # jupyter configuration
            f"mkdir -p /home/{username}/.jupyter && printf '{jupyter_config}' > /home/{username}/.jupyter/jupyter_config.json",
        ]
    )
    lifecycle_hooks = {"postStart": {"exec": {"command": ["/bin/sh", "-c", command]}}}

    extra_container_config = {
        "workingDir": f"/home/{username}",
    }

    return {
        "environment": environment,
        "lifecycle_hooks": lifecycle_hooks,
        "uid": uid,
        "gid": gid,
        "fs_gid": gid,
        "notebook_dir": f"/home/{username}",
        "extra_container_config": extra_container_config,
    }


def profile_argo_token(groups):
    # TODO: create a more robust check user's Argo-Workflow role

    if not z2jh.get_config("custom.argo-workflows-enabled"):
        return {}

    domain = z2jh.get_config("custom.external-url")
    namespace = z2jh.get_config("custom.namespace")

    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"

    base = "argo-"
    argo_sa = None

    if ANALYST in groups:
        argo_sa = base + "viewer"
    if DEVELOPER in groups:
        argo_sa = base + "developer"
    if ADMIN in groups:
        argo_sa = base + "admin"
    if not argo_sa:
        return {}

    return {
        "ARGO_BASE_HREF": "/argo",
        "ARGO_SERVER": f"{domain}:443",
        "ARGO_NAMESPACE": namespace,
        "ARGO_TOKEN": "Bearer $(HERA_TOKEN)",
        "ARGO_HTTP1": "true",  # Maybe due to traefik config, but `argo list` returns 404 without this set.  Try removing after upgrading argo past v3.4.4.
        # Hera token is needed for versions of hera released before https://github.com/argoproj-labs/hera/pull/1053 is merged
        "HERA_TOKEN": {
            "valueFrom": {
                "secretKeyRef": {
                    "name": f"{argo_sa}.service-account-token",
                    "key": "token",
                }
            }
        },
    }


def profile_conda_store_viewer_token():
    return {
        "CONDA_STORE_TOKEN": {
            "valueFrom": {
                "secretKeyRef": {
                    "name": "argo-workflows-conda-store-token",
                    "key": "conda-store-api-token",
                }
            }
        },
        "CONDA_STORE_SERVICE": {
            "valueFrom": {
                "secretKeyRef": {
                    "name": "argo-workflows-conda-store-token",
                    "key": "conda-store-service-name",
                }
            }
        },
        "CONDA_STORE_SERVICE_NAMESPACE": {
            "valueFrom": {
                "secretKeyRef": {
                    "name": "argo-workflows-conda-store-token",
                    "key": "conda-store-service-namespace",
                }
            }
        },
    }


def render_profile(
    profile, username, groups, keycloak_profilenames, groups_to_volume_mount
):
    """Render each profile for user.

    If profile is not available for given username, groups returns
    None. Otherwise profile is transformed into kubespawner profile.

    {
        display_name: "<heading for profile>",
        slug: "<longer description of profile>"
        default: "<only one profile can be default>",
        kubespawner_override: {
            # https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html
            ...
        }
    }
    """
    access = profile.get("access", "all")

    if access == "yaml":
        # check that username or groups in allowed groups for profile
        # profile.groups and profile.users can be None or empty lists, or may not be members of profile at all
        user_not_in_users = username not in set(profile.get("users", []) or [])
        user_not_in_groups = (
            set(groups) & set(profile.get("groups", []) or [])
        ) == set()
        if user_not_in_users and user_not_in_groups:
            return None
    elif access == "keycloak":
        # Keycloak mapper should provide the 'jupyterlab_profiles' attribute from groups/user
        if profile.get("display_name", None) not in keycloak_profilenames:
            return None

    profile = copy.copy(profile)
    profile_kubespawner_override = profile.get("kubespawner_override")
    profile["kubespawner_override"] = functools.reduce(
        deep_merge,
        [
            base_profile_home_mounts(username),
            base_profile_shared_mounts(groups_to_volume_mount),
            profile_conda_store_mounts(username, groups),
            base_profile_extra_mounts(),
            configure_user(username, groups),
            configure_user_provisioned_repositories(username),
            profile_kubespawner_override,
        ],
        {},
    )

    # We need to merge any env vars from the spawner with any overrides from the profile
    # This is mainly to ensure JUPYTERHUB_ANYONE/GROUP is passed through from the spawner
    # to control dashboard access.
    envvars_fixed = {**(profile["kubespawner_override"].get("environment", {}))}

    def preserve_envvars(spawner):
        # This adds in JUPYTERHUB_ANYONE/GROUP rather than overwrite all env vars,
        # if set in the spawner for a dashboard to control access.
        return {
            **envvars_fixed,
            **spawner.environment,
            **profile_argo_token(groups),
            **profile_conda_store_viewer_token(),
        }

    profile["kubespawner_override"]["environment"] = preserve_envvars

    return profile


@gen.coroutine
def render_profiles(spawner):
    # jupyterhub does not yet manage groups but it will soon
    # so for now we rely on auth_state from the keycloak
    # userinfo request to have the groups in the key
    # "auth_state.oauth_user.groups"
    auth_state = yield spawner.user.get_auth_state()

    username = auth_state["oauth_user"]["preferred_username"]

    # only return the lowest level group name
    # e.g. /projects/myproj -> myproj
    # and /developers -> developers
    groups = [Path(group).name for group in auth_state["oauth_user"]["groups"]]

    keycloak_profilenames = auth_state["oauth_user"].get("jupyterlab_profiles", [])

    groups_with_permission_to_mount = auth_state.get(
        "groups_with_permission_to_mount", []
    )

    # fetch available profiles and render additional attributes
    profile_list = z2jh.get_config("custom.profiles")
    return list(
        filter(
            None,
            [
                render_profile(
                    p,
                    username,
                    groups,
                    keycloak_profilenames,
                    groups_with_permission_to_mount,
                )
                for p in profile_list
            ],
        )
    )


c.KubeSpawner.args = ["--debug"]
c.KubeSpawner.environment = {
    **c.KubeSpawner.environment,
    "JUPYTERHUB_SINGLEUSER_APP": "jupyter_server.serverapp.ServerApp",
}
c.KubeSpawner.profile_list = render_profiles


# Utils
def deep_merge(d1, d2):
    """Deep merge two dictionaries.
    >>> value_1 = {
    'a': [1, 2],
    'b': {'c': 1, 'z': [5, 6]},
    'e': {'f': {'g': {}}},
    'm': 1,
    }.

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


def generate_nss_files(users, groups):
    etc_passwd = []
    passwd_format = "{username}:x:{uid}:{gid}:{username}:/home/{username}:/bin/bash"
    for user in users:
        etc_passwd.append(passwd_format.format(**user))

    etc_group = []
    group_format = "{groupname}:x:{gid}:"
    for group in groups:
        etc_group.append(group_format.format(**group))

    return "\n".join(etc_passwd), "\n".join(etc_group)
