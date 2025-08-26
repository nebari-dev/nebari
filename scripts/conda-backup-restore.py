#!/usr/bin/env python3
"""
conda-store backup and restore CLI tool
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from conda_store.api import CondaStoreAPI, CondaStoreAPIError
from conda_store._internal import utils


# TODO(asmacdo) this could potentially be moved to upstream conda-store
# I'll ask in the community meeting if they want it before putting in the time
class ExtendedCondaStoreAPI(CondaStoreAPI):
    """Extended client with lockfile and idempotent restore support"""

    async def get_environment_lockfile(
        self, namespace: str, environment_name: str
    ) -> str:
        """Get current lockfile for an environment"""
        async with self.session.get(
            utils.ensure_slash(
                self.api_url
                / "environment"
                / namespace
                / environment_name
                / "conda-lock.yaml"
            )
        ) as response:
            if response.status != 200:
                raise CondaStoreAPIError(
                    f"Error getting lockfile for {namespace}/{environment_name}"
                )
            return await response.text()

    async def create_environment_from_lockfile(
        self,
        namespace: str,
        specification: str,
        environment_name: str = "",
        environment_description: str = "",
    ):
        """Create environment from lockfile specification"""
        async with self.session.post(
            utils.ensure_slash(self.api_url / "specification"),
            json={
                "namespace": namespace,
                "specification": specification,
                "is_lockfile": True,
                "environment_name": environment_name,
                "environment_description": environment_description,
            },
        ) as response:
            data = await response.json()
            if response.status != 200:
                message = data["message"]
                raise CondaStoreAPIError(
                    f"Error creating environment from lockfile in namespace {namespace}\nReason {message}"
                )
            return data["data"]["build_id"]

    async def environment_exists(self, namespace: str, environment_name: str) -> bool:
        """Check if environment exists"""
        try:
            await self.get_environment(namespace=namespace, name=environment_name)
            return True
        except CondaStoreAPIError:
            return False


async def _backup_environment(
    conda_store: ExtendedCondaStoreAPI,
    namespace_name: str,
    env_name: str,
    backup_dir: Path,
) -> bool:
    """Backup a single environment. Returns True if successful."""
    try:
        # Create namespace subdirectory
        namespace_dir = backup_dir / namespace_name
        namespace_dir.mkdir(exist_ok=True)

        # Get current lockfile for environment (not build-specific)
        lockfile_content = await conda_store.get_environment_lockfile(
            namespace_name, env_name
        )

        # Save lockfile with environment name
        filename = f"{env_name}.conda-lock.yaml"
        filepath = namespace_dir / filename

        with open(filepath, "w") as f:
            f.write(lockfile_content)

        print(f"✓ {namespace_name}/{env_name} -> {filepath}")
        return True

    except Exception as e:
        print(f"✗ Failed to backup {namespace_name}/{env_name}: {e}")
        return False


async def backup_environments(
    conda_store: ExtendedCondaStoreAPI,
    backup_dir: Path,
    target_env: Optional[str] = None,
):
    """Backup all environments or a specific one"""

    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    timestamped_backup_dir = backup_dir / f"{timestamp}"
    timestamped_backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created backup directory: {timestamped_backup_dir}")

    backup_count = 0
    skip_count = 0

    # If specific environment specified, backup just that one
    if target_env:
        if "/" not in target_env:
            print("Error: Environment must be specified as 'namespace/name'")
            return

        target_namespace, target_name = target_env.split("/", 1)
        print(f"\n=== Backing up {target_env} ===")

        success = await _backup_environment(
            conda_store, target_namespace, target_name, timestamped_backup_dir
        )
        if success:
            backup_count = 1
        else:
            skip_count = 1
    else:
        # Backup all environments
        print("\n=== Backing up all environments ===")
        environments = await conda_store.list_environments(
            status=None, artifact=None, packages=[]
        )

        for env in environments:
            namespace_name = env["namespace"]["name"]
            env_name = env["name"]

            success = await _backup_environment(
                conda_store, namespace_name, env_name, timestamped_backup_dir
            )
            if success:
                backup_count += 1
            else:
                skip_count += 1

    print(f"\n=== Backup Summary ===")
    print(f"Successfully backed up: {backup_count} environments")
    print(f"Skipped: {skip_count} environments")
    print(f"Backup directory: {timestamped_backup_dir.absolute()}")


async def _restore_environment(
    conda_store: ExtendedCondaStoreAPI,
    namespace_name: str,
    env_name: str,
    lockfile_path: Path,
    force: bool = False,
) -> Optional[str]:
    """Restore a single environment. Returns 'restored', 'skipped', or None for error."""
    try:
        # Check if environment already exists (idempotent check)
        exists = await conda_store.environment_exists(namespace_name, env_name)

        if exists and not force:
            print(
                f"⚠ {namespace_name}/{env_name} already exists (use --force to recreate)"
            )
            return "skipped"

        # Read lockfile
        lockfile_content = lockfile_path.read_text()

        print(f"{'↻' if exists else '+'} Restoring {namespace_name}/{env_name}...")

        # Create/update environment from lockfile
        build_id = await conda_store.create_environment_from_lockfile(
            namespace=namespace_name,
            specification=lockfile_content,
            environment_name=env_name,
            environment_description="Restored from backup",
        )

        print(f"✓ {namespace_name}/{env_name} -> build {build_id}")
        return "restored"

    except Exception as e:
        print(f"✗ Failed to restore {namespace_name}/{env_name}: {e}")
        return None


async def restore_environments(
    conda_store: ExtendedCondaStoreAPI,
    backup_dir: Path,
    target_env: Optional[str] = None,
    force: bool = False,
):
    """Restore environments from latest backup"""

    # Find latest backup directory
    backup_dirs = sorted([d for d in backup_dir.glob("*") if d.is_dir()], reverse=True)
    if not backup_dirs:
        print("No backup directories found")
        return

    latest_backup = backup_dirs[0]
    print(f"Restoring from: {latest_backup}")

    restore_count = 0
    skip_count = 0
    error_count = 0

    # If specific environment specified, restore just that one
    if target_env:
        if "/" not in target_env:
            print("Error: Environment must be specified as 'namespace/name'")
            return

        target_namespace, target_name = target_env.split("/", 1)
        lockfile_path = (
            latest_backup / target_namespace / f"{target_name}.conda-lock.yaml"
        )

        if not lockfile_path.exists():
            print(f"Error: Backup not found for {target_env}")
            return

        result = await _restore_environment(
            conda_store, target_namespace, target_name, lockfile_path, force
        )
        if result == "restored":
            restore_count = 1
        elif result == "skipped":
            skip_count = 1
        else:
            error_count = 1
    else:
        # Restore all environments
        for namespace_dir in latest_backup.iterdir():
            if not namespace_dir.is_dir():
                continue

            namespace_name = namespace_dir.name

            # Process each lockfile in namespace
            for lockfile_path in namespace_dir.glob("*.conda-lock.yaml"):
                env_name = lockfile_path.stem.replace(".conda-lock", "")

                result = await _restore_environment(
                    conda_store, namespace_name, env_name, lockfile_path, force
                )
                if result == "restored":
                    restore_count += 1
                elif result == "skipped":
                    skip_count += 1
                else:
                    error_count += 1

    print(f"\n=== Restore Summary ===")
    print(f"Successfully restored: {restore_count} environments")
    print(f"Skipped (already exist): {skip_count} environments")
    print(f"Errors: {error_count} environments")


async def main():
    parser = argparse.ArgumentParser(description="conda-store backup and restore tool")
    parser.add_argument("command", choices=["backup", "restore"], help="Command to run")
    parser.add_argument(
        "--backup-dir",
        default="./conda_store_backups",
        help="Backup directory (default: ./conda_store_backups)",
    )
    parser.add_argument(
        "--environment",
        help="Specific environment to backup/restore (format: namespace/name)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force restore even if environment exists"
    )

    args = parser.parse_args()

    # Configuration from environment
    conda_store_url = os.getenv("CONDA_STORE_URL")
    api_token = os.getenv("CONDA_STORE_TOKEN")

    if not conda_store_url:
        print("Error: CONDA_STORE_URL environment variable must be set")
        sys.exit(1)

    if not api_token:
        print("Error: CONDA_STORE_TOKEN environment variable must be set")
        sys.exit(1)

    backup_dir = Path(args.backup_dir)

    # Initialize API client
    async with ExtendedCondaStoreAPI(
        conda_store_url=conda_store_url,
        auth_type="token",
        api_token=api_token,
        verify_ssl=True,
    ) as conda_store:

        try:
            if args.command == "backup":
                await backup_environments(conda_store, backup_dir, args.environment)
            elif args.command == "restore":
                await restore_environments(
                    conda_store, backup_dir, args.environment, args.force
                )

        except Exception as e:
            print(f"Error: {e}")
            raise
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
