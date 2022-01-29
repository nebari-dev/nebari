import logging
import os
import tempfile

from qhub.utils import timer, check_cloud_credentials
from qhub.provider import terraform
from qhub.state import terraform_state_sync

logger = logging.getLogger(__name__)


def destroy_01_terraform_state(config):
    directory = 'stages/01-terraform-state'

    if config['provider'] == "local":
        pass
    elif config['provider'] == 'do':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['digital_ocean']['region']
            })
    elif config['provider'] == 'gcp':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['google_cloud_platform']['region']
            })
    elif config['provider'] == 'azure':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['azure']['region'],
                'storage_account_postfix': config['azure']['storage_account_postfix'],
            })
    elif config['provider'] == 'aws':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
            })
    else:
        raise NotImplementedError(f'provider {config["provider"]} not implemented for directory={directory}')


def destroy_02_infrastructure(config):
    directory = 'stages/02-infrastructure'

    if config['provider'] == "local":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                "kube_context": config['local'].get('kube_context')
            })
    elif config['provider'] == 'do':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['digital_ocean']['region'],
                'kubernetes_version': config['digital_ocean']['kubernetes_version'],
                'node_groups': config['digital_ocean']['node_groups'],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            })
    elif config['provider'] == 'gcp':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['google_cloud_platform']['region'],
                'project_id': config['google_cloud_platform']['project'],
                'node_groups': [{'name': key, 'min_size': value['min_nodes'], 'max_size': value['max_nodes'], **value} for key, value in config['google_cloud_platform']['node_groups'].items()],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            })
    elif config['provider'] == 'azure':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['azure']['region'],
                'kubernetes_version': config['azure']['kubernetes_version'],
                'node_groups': config['azure']['node_groups'],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            })
    elif config['provider'] == 'aws':
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'node_groups': [{'name': key, 'min_size': value['min_nodes'], 'desired_size': value['min_nodes'], 'max_size': value['max_nodes'], 'gpu': value.get('gpu', False), 'instance_type': value['instance']} for key, value in config['amazon_web_services']['node_groups'].items()],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            })
    else:
        raise NotImplementedError(f'provider {config["provider"]} not implemented for directory={directory}')


def destroy_configuration(config):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'qhub deploy' to re-install infrastructure using same config file\n"""
    )

    with timer(logger, "destroying QHub"):
        # 01 Check Environment Variables
        check_cloud_credentials(config)

        destroy_02_infrastructure(config)
        destroy_01_terraform_state(config)
