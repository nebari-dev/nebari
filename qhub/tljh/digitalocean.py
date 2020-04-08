"""
Setup & tear down TLJH instances in da cloud
"""
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import MultiStepDeployment, ScriptDeployment
from ..utils import create_keypair
import os

INSTALL_SCRIPT = """#!/bin/bash
curl https://raw.githubusercontent.com/jupyterhub/the-littlest-jupyterhub/master/bootstrap/bootstrap.py \
  | sudo python3 - \
    --admin yuvipanda
"""

class DigitalOceanProvisioner:
    # FIXME: Make this inherently async
    def __init__(self, access_token):
        self.driver = get_driver(Provider.DIGITAL_OCEAN)(access_token, api_version='v2')

    def sizes(self):
        """
        Return recommended sizes for TLJH
        """
        return self.driver.list_sizes()

    def regions(self):
        """
        Return recommended regions for TLJH
        """
        return self.driver.list_locations()

    def sizes(self):
        """
        Return recommended node sizes for TLJH

        Minimum requirement is 1.5G
        """
        return [s for s in self.driver.list_sizes() if s.ram > (1.5 * 1024)]

    def image(self):
        """
        Return image to be used for setting up TLJH
        """
        for image in self.driver.list_images():
            if image.extra.get('slug') == 'ubuntu-18-04-x64':
                return image

        raise ValueError("Supported ubuntu image not found")

    def ensure_keypair(self, name, public_key):
        """
        Ensure that keypair with given public_key exists

        Returns keypair id
        """
        # FIXME: Make sure it is obvious the keypair is created by qhub
        existing_kps = self.driver.list_key_pairs()
        for kp in existing_kps:
            if kp.public_key == public_key:
                return kp.extra['id']

        kp = self.driver.create_key_pair(name, public_key)
        return kp.extra['id']

    def create(self, name, keypair_id):
        node = self.driver.create_node(
            name, self.sizes()[0],
            self.image(), self.regions()[0],
            ex_user_data=INSTALL_SCRIPT,
            ex_create_attr={
                'tags': ['creator:qhub'],
                'ssh_keys': [keypair_id]
            }
        )
        print(node)
        print(self.driver.wait_until_running([node]))



def main():
    name = 'test-12'
    # FIXME: Read this securely from users
    token = os.environ['DIGITALOCEAN_TOKEN']
    # FIXME: Make this configurable
    private_key, public_key = create_keypair(name)
    with open(name, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(private_key)
    provisioner = DigitalOceanProvisioner(token)
    provisioner.create(name, provisioner.ensure_keypair(name, public_key))

if __name__ == '__main__':
    main()
