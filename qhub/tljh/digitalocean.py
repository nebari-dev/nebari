"""
Setup & tear down TLJH instances in da cloud
"""
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from ..utils import create_keypair
import os

INSTALL_SCRIPT = """#!/bin/bash
curl https://raw.githubusercontent.com/jupyterhub/the-littlest-jupyterhub/master/bootstrap/bootstrap.py \
  | sudo python3 - \
    --admin yuvipanda
"""

class DigitalOceanProvisioner:
    def __init__(self, access_token, threadpool):
        self.driver = get_driver(Provider.DIGITAL_OCEAN)(access_token, api_version='v2')
        self.threadpool = threadpool

    def run_in_executor(self, func, *args, **kwargs):
        """
        Run func(*args, **kwargs) in current threadpool.

        Returns an Awaitable, which can be awaited to get the result of func

        IMPORTANT INFORMATION TO AVOID DEADLOCKS

        Code should operate on the assumption that the ThreadPool has only one
        Thread. This *will* cause deadlocks if we nest run_in_executor calls -
        a function running on the thread will block on trying to run another
        function on the thread, and be stuck indefinitely. So, we should try
        make sure that doesn't happen.
        """
        # @todo: [FIXME] Detect threadpool deadlocks early & throw exceptions
        # ThreadPoolExecutor(1) is the common case, and *will* deadlock if run_in_executor
        # is called while another run_in_executor is in the stack - the two caller will
        # just wait forever for the called function to be scheduled, and the called function
        # will forever wait for the thread to be made available. We should inspect the
        # stack (if it is cheap), and error out if we detect this is happening. Much
        # rather get an unexpected exception than an unexpected deadlock
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(self.threadpool, partial(func, *args, **kwargs))

    async def regions(self):
        """
        Return recommended regions for TLJH
        """
        return await self.run_in_executor(self.driver.list_locations)

    async def sizes(self):
        """
        Return recommended node sizes for TLJH

        Minimum requirement is 1.5G
        """
        return [s for s in await self.run_in_executor(self.driver.list_sizes) if s.ram > (1.5 * 1024)]

    async def image(self):
        """
        Return image to be used for setting up TLJH
        """
        for image in await self.run_in_executor(self.driver.list_images):
            if image.extra.get('slug') == 'ubuntu-18-04-x64':
                return image

        raise ValueError("Supported ubuntu image not found")

    async def ensure_keypair(self, name, public_key):
        """
        Ensure that keypair with given public_key exists

        Returns keypair id
        """
        # FIXME: Make sure it is obvious the keypair is created by qhub
        existing_kps = await self.run_in_executor(self.driver.list_key_pairs)
        for kp in existing_kps:
            if kp.public_key == public_key:
                return kp.extra['id']

        kp = await self.run_in_executor(self.driver.create_key_pair, name, public_key)
        return kp.extra['id']

    async def create(self, name, keypair_id):
        """
        Create a TLJH with given name

        SSH as root will be enabled, with access granted to key specified by keypair_id
        """
        node = await self.run_in_executor(self.driver.create_node,
            name, (await self.sizes())[0],
            await self.image(), (await self.regions())[0],
            ex_user_data=INSTALL_SCRIPT,
            ex_create_attr={
                'tags': ['creator:qhub'],
                'ssh_keys': [keypair_id]
            }
        )
        return await self.run_in_executor(self.driver.wait_until_running, [node])


async def main():
    name = 'test-15'
    # FIXME: Read this securely from users
    token = os.environ['DIGITALOCEAN_TOKEN']
    # FIXME: Make this configurable
    private_key, public_key = create_keypair(name)
    with open(name, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(private_key)
    provisioner = DigitalOceanProvisioner(token, ThreadPoolExecutor(1))
    print(await provisioner.create(name, await provisioner.ensure_keypair(name, public_key)))

if __name__ == '__main__':
    asyncio.run(main())
