import os

import z2jh
from tornado import gen


def base_profile_mounts(username, groups):
    # kubernetes does not allow multiple volume sections
    # for the same pvc thus there are multiple checks within
    # (home_pvc_name != shared_pvc_name)
    home_pvc_name = z2jh.get_config('custom.home-pvc')
    shared_pvc_name = z2jh.get_config('custom.shared-pvc')

    pvc_home_mount_path = 'home/{username}'
    pod_home_mount_path = '/home/jovyan'

    pvc_shared_mount_path = 'share/{group}'
    pod_shared_mount_path = '/share/{group}'

    extra_pod_config = {
        'volumes': [
            {
                'name': 'home',
                'persistentVolumeClaim': {
                    'claimName': home_pvc_name,
                }
            },
        ]
    }
    if home_pvc_name != shared_pvc_name:
        extra_pod_config['volumes'].append({
            'name': 'shared',
            'persistentVolumeClaim': {
                'claimName': shared_pvc_name
            }
        })

    extra_container_config = {
        'volumeMounts': [{
            'mountPath': pod_home_mount_path.format(username=username),
            'name': 'home',
            'subPath': pvc_home_mount_path.format(username=username)
        }] + [{
            'mountPath': pod_shared_mount_path.format(group=group),
            'name': 'shared' if home_pvc_name != shared_pvc_name else 'home',
            'subPath': pvc_shared_mount_path.format(group=group),
        } for group in groups]
    }

    MKDIR_OWN_DIRECTORY = 'mkdir -p {base_dir}/{path} && chmod 777 {base_dir}/{path}'
    command = ' && '.join([
        MKDIR_OWN_DIRECTORY.format(
            base_dir='/home-mnt',
            path=pvc_home_mount_path.format(username=username)
    )] + [
        MKDIR_OWN_DIRECTORY.format(
            base_dir='/shared-mnt' if home_pvc_name != shared_pvc_name else '/home-mnt',
            path=pvc_shared_mount_path.format(group=group)) for group in groups])

    init_containers = [{
        'name': 'init-mounts',
        'image': 'busybox:1.31',
        'command': ['sh', '-c', command],
        'securityContext': {
            'runAsUser': 0
        },
        'volumeMounts': [{
            'mountPath': "/home-mnt",
            'name': 'home'
        }]
    }]
    if home_pvc_name != shared_pvc_name:
        init_containers[0]['volumeMounts'].append({
            'mountPath': "/shared-mnt",
            'name': 'shared'
        })

    return {
        'extra_pod_config': extra_pod_config,
        'extra_container_config': extra_container_config,
        'init_containers': init_containers,
    }


@gen.coroutine
def calculate_profiles(spawner):
    # jupyterhub does not yet manage groups but it will soon
    # so for now we rely on auth_state from the keycloak
    # userinfo request to have the groups in the key
    # "auth_state.oauth_user.groups"
    auth_state = yield spawner.user.get_auth_state()
    spawner.log.error(str(auth_state))

    username = auth_state['oauth_user']['preferred_username']
    # only return groups that match '/projects/[.^/]+'
    groups = [os.path.basename(_) for _ in auth_state['oauth_user']['groups'] if os.path.dirname(_) == '/projects']
    spawner.log.error(f'user info: {username} {groups}')

    # shared confituration for user
    kubespawner_override = base_profile_mounts(username, groups)

    # kubespawner_override options are available
    # https://github.com/jupyterhub/kubespawner/blob/main/kubespawner/spawner.py
    return [{
        'display_name': 'Training Env - Python',
        'slug': 'training-python',
        'default': True,
        'kubespawner_override': kubespawner_override
    }]

c.KubeSpawner.profile_list = calculate_profiles



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
