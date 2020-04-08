"""
Setup & tear down TLJH instances in da cloud
"""
import asyncio
import asyncssh
import argparse
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from jsonschema import validate
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
    def __init__(self, auth, threadpool):
        validate(auth, schema=DigitalOceanProvisioner.auth_schema())
        self.driver = get_driver(Provider.DIGITAL_OCEAN)(auth['access_token'], api_version='v2')
        self.threadpool = threadpool

    @classmethod
    def auth_schema(cls):
        """
        Define what authentication parameters this provisioner needs

        Returns a JSON Schema of properties needed by auth
        """
        # FIXME: Is this sane?
        # JSON Schema is transferable between Python and JS. This is probably going to
        # be important when we build a web interface? Unclear. This will probably be in flux.
        return {
            'type': 'object',
            'properties': {
                'access_token': {
                    'type': 'string',
                    'description': """
                    Personal Access Token with write permissions from the DigitalOcean website.

                    See https://www.digitalocean.com/docs/apis-clis/api/create-personal-access-token/
                    for details on how to fetch this.
                    """,
                }
            }
        }


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

    async def ensure_keypair(self, name, key: asyncssh.SSHKey):
        """
        Ensure that keypair with given key exists

        Returns key fingerprint
        """
        # FIXME: Make sure it is obvious the keypair is created by qhub
        existing_kps = await self.run_in_executor(self.driver.list_key_pairs)
        for kp in existing_kps:
            if kp.fingerprint == key.get_fingerprint('md5'):
                return kp.fingerprint

        kp = await self.run_in_executor(self.driver.create_key_pair, name, key.export_public_key('openssh').decode('utf-8'))
        return kp.fingerprint

    async def create(self, name, key_fingerprint: str):
        """
        Create a TLJH with given name

        SSH as root will be enabled, with access granted to key specified by key_fingerprint
        """
        node = await self.run_in_executor(self.driver.create_node,
            name, (await self.sizes())[0],
            await self.image(), (await self.regions())[0],
            ex_user_data=INSTALL_SCRIPT,
            ex_create_attr={
                'tags': ['creator:qhub'],
                'ssh_keys': [key_fingerprint]
            }
        )
        completed_node, public_ip = (await self.run_in_executor(self.driver.wait_until_running, [node]))[0]

        return completed_node
