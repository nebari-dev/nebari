BASE_CONFIGURATION = {
    'project_name': None,
    'provider': None,
    'ci_cd': 'github-actions',
    'domain': None,
    'security': {
        'authenication': None,
        'users': {
            'costrouc': {
                'uid': 1000,
                'primary_group': 'users',
                'secondary_groups': [
                    'admin'
                ]
            }
        },
        'groups': {
            'users': {
                'gid': 100
            },
            'admin': {
                'gid': 101
            }
        }
    },
    'default_images': {
        'jupyterhub': 'quansight/qhub-jupyterhub:1abd4efb8428a9d851b18e89b6f6e5ef94854334',
        'jupyterlab': 'quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334',
        'dask_worker': 'quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334',
    },
    'storage': {
        'conda_store': '20Gi',
        'shared_filesystem': '10Gi',
    }
}

OAUTH_GITHUB = {
    'type': 'GitHub',
    'config': {
        'client_id': 'PLACEHOLDER',
        'client_secret': 'PLACEHOLDER',
        'oauth_callback_url': 'PLACEHOLDER',
    }
}

OAUTH_AUTH0 = {
    'type': 'Auth0',
    'config': {
        'client_id': 'PLACEHOLDER',
        'client_secret': 'PLACEHOLDER',
        'oauth_callback_url': 'PLACEHOLDER',
        'scope': ['openid', 'email', 'profile'],
        'auth0_subdomain': 'PLACEHOLDER',
    }
}

DIGITAL_OCEAN = {
    'region': 'nyc3',
    'kubernetes_version': '1.18.8-do.0',
    'node_groups': {
        'general': {
            'instance': 's-2vcpu-4gb',
            'min_nodes': 1,
            'max_nodes': 1
        },
        'user': {
            'instance': 's-2vcpu-4gb',
            'min_nodes': 1,
            'max_nodes': 4
        },
        'worker': {
            'instance': 's-2vcpu-4gb',
            'min_nodes': 1,
            'max_nodes': 4,
        }
    }
}

GOOGLE_PLATFORM = {
    'project': 'PLACEHOLDER',
    'region': 'us-central1',
    'zone': 'us-central1-c',
    'availability_zones': ['us-central1-c'],
    'kubernetes_version': '1.14.10-gke.31',
    'node_groups': {
        'general': {
            'instance': 'n1-standard-2',
            'min_nodes': 1,
            'max_nodes': 1
        },
        'user': {
            'instance': 'n1-standard-2',
            'min_nodes': 1,
            'max_nodes': 4
        },
        'worker': {
            'instance': 'n1-standard-2',
            'min_nodes': 1,
            'max_nodes': 4,
        }
    }
}

DEFAULT_PROFILES = {
    'jupyterhub': [
        {
            'display_name': 'Small Instance',
            'description': 'Stable environment with 1 cpu / 1 GB ram',
            'default': True,
            'kubespawner_override': {
                'cpu_limit': 1,
                'cpu_guarantee': 1,
                'mem_limit': '1G',
                'mem_guarantee': '1G',
                'image': 'quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334'
            }
        },
        {
            'display_name': 'Medium Instance',
            'description': 'Stable environment with 1.5 cpu / 2 GB ram',
            'kubespawner_override': {
                'cpu_limit': 1.5,
                'cpu_guarantee': 1.25,
                'mem_limit': '2G',
                'mem_guarantee': '2G',
                'image': 'quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334'
            }
        }
    ],
    'dask_worker': {
        'Small Worker': {
            'worker_cores_limit': 1,
            'worker_cores': 1,
            'worker_memory_limit': '1G',
            'worker_memory': '1G',
            'image': 'quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334'
        },
        'Medium Worker': {
            'worker_cores_limit': 1.5,
            'worker_cores': 1.25,
            'worker_memory_limit': '2G',
            'worker_memory': '2G',
            'image': 'quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334'
        }
    }
}

DEFAULT_ENVIRONMENTS = {
    'environment-default.yaml': {
        'name': 'default',
        'channels': [
            'conda-forge',
            'defaults'
        ],
        'dependencies': [
            'python=3.8',
            'ipykernel',
            'ipywidgets',
            'dask==2.14.0',
            'distributed==2.14',
            'dask-gateway=0.6.1',
            'numpy',
            'numba',
            'pandas'
        ]
    }
}


def initialize_config(project_name, qhub_domain, cloud_provider, ci_provider, oauth_provider):
    config = BASE_CONFIGURATION
    config['provider'] = cloud_provider
    config['project_name'] = project_name
    cofnig
