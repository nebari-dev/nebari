import asyncio
import argparse
import os
import asyncssh
from concurrent.futures import ThreadPoolExecutor

from ..utils import create_keypair, schema_to_subparser
from .import DigitalOceanProvisioner


async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    schema_to_subparser(
        DigitalOceanProvisioner.auth_schema(),
        subparsers.add_parser('digitalocean')
    )

    parser.add_argument(
        'name',
        help='Name of the TLJH instance to be created'
    )

    args = parser.parse_args()


    key: asyncssh.SSHKey = asyncssh.generate_private_key('ssh-rsa')
    with open(args.name, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(key.export_private_key().decode())

    provisioner = DigitalOceanProvisioner({'access_token': args.access_token}, ThreadPoolExecutor(1))

    completed_node = await provisioner.create(args.name, await provisioner.ensure_keypair(args.name, key))
    print(completed_node)

def cli_start():
    """
    Sync function to be called from entry_points' console_scripts

    Can't seem to have console_scripts call just the file, needs a specific
    function. The function can't be async, so we have this stub.
    """
    asyncio.run(main())

if __name__ == '__main__':
    cli_start()