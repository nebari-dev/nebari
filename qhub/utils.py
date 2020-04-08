import argparse

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