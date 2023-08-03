import argparse
import json
import logging
import sys
from pathlib import Path

from _nebari.keycloak import get_keycloak_admin_from_config

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Export users and groups from Nebari.")
    parser.add_argument("-c", "--config", help="nebari configuration", required=True)
    args = parser.parse_args()

    handle_keycloak_export(args)


def handle_keycloak_export(args):
    config_filename = Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    keycloak_admin = get_keycloak_admin_from_config(config_filename)

    realm = {"id": "nebari", "realm": "nebari"}

    def process_user(u):
        uid = u["id"]
        memberships = keycloak_admin.get_user_groups(uid)

        del u["id"]
        u["groups"] = [g["name"] for g in memberships]
        return u

    realm["users"] = [process_user(u) for u in keycloak_admin.get_users()]

    realm["groups"] = [
        {"name": g["name"], "path": g["path"]}
        for g in keycloak_admin.get_groups()
        if g["name"] not in {"users", "admin"}
    ]

    json.dump(realm, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
