import argparse

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend


def schema_to_subparser(schema: dict, subparser: argparse.ArgumentParser):
    """
    Setup an argparser with properties from a JSON Schema

    This *mutates* the subparser, since that is how argparser seems to work.
    """
    # FIXME: validate the schema is valid json-schema
    for property, spec in schema['properties'].items():
        if spec['type'] != 'string':
            raise ValueError(f'Only string properties supported now, {property} is of type {spec["type"]}')

        subparser.add_argument(
            f'--{property}',
            help=spec['description'],
            required=True
        )


def create_keypair(name):
    """
    Generate an RSA SSH Keypair in OpenSSH format

    Returns a (private_key, public_key)
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        # FIXME: Document this number?
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    return private_key.decode('utf-8'), public_key.decode('utf-8')