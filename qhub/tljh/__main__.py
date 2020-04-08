import asyncio
import argparse
import os
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

    # FIXME: Make this configurable
    private_key, public_key = create_keypair(args.name)
    with open(args.name, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(private_key)

    provisioner = DigitalOceanProvisioner({'access_token': args.access_token}, ThreadPoolExecutor(1))

    print(await provisioner.create(args.name, await provisioner.ensure_keypair(args.name, public_key)))

def cli_start():
    """
    Sync function to be called from entry_points' console_scripts

    Can't seem to have console_scripts call just the file, needs a specific
    function. The function can't be async, so we have this stub.
    """
    asyncio.run(main())

if __name__ == '__main__':
    cli_start()