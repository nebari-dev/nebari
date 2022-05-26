import copy
import functools
import json
import os

import z2jh
from tornado import gen


def base_profile_home_mounts(username):
    """Configure the home directory mount for user

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
        "mkdir -p /mnt/{path} && chmod 777 /mnt/{path} && cp -r /etc/skel/. /mnt/{path}"
    )
    command = MKDIR_OWN_DIRECTORY.format(
        path=pvc_home_mount_path.format(username=username)
    )
    init_containers = [
        {
            "name": "initialize-home-mount",
            "image": "busybox:1.31",
            "command": ["sh", "-c", command],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [
                {"mountPath": "/mnt", "name": "home"},
                {"mountPath": "/etc/skel", "name": "skel"},
            ],
        }
    ]
    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
        "init_containers": init_containers,
    }


def base_profile_shared_mounts(groups):
    """Configure the group directory mounts for user

    Ensure that {shared}/{group} directory exists and user has
    permissions to read/write/execute. Kubernetes does not allow the
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

    extra_container_config = {
        "volumeMounts": [
            {
                "mountPath": pod_shared_mount_path.format(group=group),
                "name": "shared" if home_pvc_name != shared_pvc_name else "home",
                "subPath": pvc_shared_mount_path.format(group=group),
            }
            for group in groups
        ]
    }

    MKDIR_OWN_DIRECTORY = "mkdir -p /mnt/{path} && chmod 777 /mnt/{path}"
    command = " && ".join(
        [
            MKDIR_OWN_DIRECTORY.format(path=pvc_shared_mount_path.format(group=group))
            for group in groups
        ]
    )
    init_containers = [
        {
            "name": "initialize-shared-mounts",
            "image": "busybox:1.31",
            "command": ["sh", "-c", command],
            "securityContext": {"runAsUser": 0},
            "volumeMounts": [
                {
                    "mountPath": "/mnt",
                    "name": "shared" if home_pvc_name != shared_pvc_name else "home",
                }
            ],
        }
    ]
    return {
        "extra_pod_config": extra_pod_config,
        "extra_container_config": extra_container_config,
        "init_containers": init_containers,
    }


def profile_conda_store_mounts(username, groups):
    """Configure the conda_store environment directories mounts for
    user

    Ensure that {shared}/{group} directory exists and user has
    permissions to read/write/execute.

    """
    conda_store_pvc_name = z2jh.get_config("custom.conda-store-pvc")
    conda_store_mount = z2jh.get_config("custom.conda-store-mount")

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

    conda_store_namespaces = [username, "filesystem", "default"] + groups
    extra_container_config = {
        "volumeMounts": [
            {
                "mountPath": os.path.join(conda_store_mount, namespace),
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
                    "mountPath": "/mnt",
                    "name": "conda-store",
                }
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
            {
                "name": volume["name"],
                "persistentVolumeClaim": {"claimName": volume["name"]},
            }
            if volume["kind"] == "persistentvolumeclaim"
            else {"name": volume["name"], "configMap": {"name": volume["name"]}}
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
    condarc = json.dumps(
        {
            "envs_dirs": [
                f"/home/conda/{_}/envs"
                for _ in [
                    username,
                    "filesystem",
                    "default",
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
            f"ln -sfn /shared /home/{username}/shared"
            if groups
            else f"rm -f /home/{username}/shared",
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


def render_profile(profile, username, groups, keycloak_profilenames):
    """Render each profile for user

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
            base_profile_shared_mounts(groups),
            profile_conda_store_mounts(username, groups),
            base_profile_extra_mounts(),
            configure_user(username, groups),
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
        return {**envvars_fixed, **spawner.environment}

    profile["kubespawner_override"]["environment"] = preserve_envvars

    return profile


@gen.coroutine
def render_profiles(spawner):
    # jupyterhub does not yet manage groups but it will soon
    # so for now we rely on auth_state from the keycloak
    # userinfo request to have the groups in the key
    # "auth_state.oauth_user.groups"
    auth_state = yield spawner.user.get_auth_state()
    spawner.log.error(str(auth_state))

    username = auth_state["oauth_user"]["preferred_username"]
    # only return the lowest level group name
    # e.g. /projects/myproj -> myproj
    # and /developers -> developers
    groups = [os.path.basename(_) for _ in auth_state["oauth_user"]["groups"]]
    spawner.log.error(f"user info: {username} {groups}")

    keycloak_profilenames = auth_state["oauth_user"].get("jupyterlab_profiles", [])

    # fetch available profiles and render additional attributes
    profile_list = z2jh.get_config("custom.profiles")
    return list(
        filter(
            None,
            [
                render_profile(p, username, groups, keycloak_profilenames)
                for p in profile_list
            ],
        )
    )


c.KubeSpawner.profile_list = render_profiles


# Utils
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
