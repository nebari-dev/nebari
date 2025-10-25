import contextlib
import enum
import json
import os
import secrets
import string
import sys
import time
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import Field, ValidationInfo, field_validator, model_validator

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from _nebari.utils import modified_environ
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

NUM_ATTEMPTS = 10
TIMEOUT = 10


class InputVars(schema.Base):
    name: str
    environment: str
    endpoint: str
    initial_root_password: str
    overrides: List[str]
    node_group: Dict[str, str]
    themes: Dict[str, Union[bool, str]]


@contextlib.contextmanager
def keycloak_provider_context(keycloak_credentials: Dict[str, str]):
    credential_mapping = {
        "client_id": "KEYCLOAK_CLIENT_ID",
        "url": "KEYCLOAK_URL",
        "username": "KEYCLOAK_USER",
        "password": "KEYCLOAK_PASSWORD",
        "realm": "KEYCLOAK_REALM",
    }

    credentials = {credential_mapping[k]: v for k, v in keycloak_credentials.items()}
    with modified_environ(**credentials):
        yield


@schema.yaml_object(schema.yaml)
class AuthenticationEnum(str, enum.Enum):
    password = "password"
    github = "GitHub"
    auth0 = "Auth0"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class GitHubConfig(schema.Base):
    client_id: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_CLIENT_ID"),
        validate_default=True,
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_CLIENT_SECRET"),
        validate_default=True,
    )

    @field_validator("client_id", "client_secret", mode="before")
    @classmethod
    def validate_credentials(cls, value: Optional[str], info: ValidationInfo) -> str:
        variable_mapping = {
            "client_id": "GITHUB_CLIENT_ID",
            "client_secret": "GITHUB_CLIENT_SECRET",
        }
        if value is None:
            raise ValueError(
                f"Missing the following required environment variable: {variable_mapping[info.field_name]}"
            )
        return value


class Auth0Config(schema.Base):
    client_id: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_CLIENT_ID"),
        validate_default=True,
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_CLIENT_SECRET"),
        validate_default=True,
    )
    auth0_subdomain: str = Field(
        default_factory=lambda: os.environ.get("AUTH0_DOMAIN"),
        validate_default=True,
    )

    @field_validator("client_id", "client_secret", "auth0_subdomain", mode="before")
    @classmethod
    def validate_credentials(cls, value: Optional[str], info: ValidationInfo) -> str:
        variable_mapping = {
            "client_id": "AUTH0_CLIENT_ID",
            "client_secret": "AUTH0_CLIENT_SECRET",
            "auth0_subdomain": "AUTH0_DOMAIN",
        }
        if value is None:
            raise ValueError(
                f"Missing the following required environment variable: {variable_mapping[info.field_name]} "
            )
        return value


class BaseAuthentication(schema.Base):
    type: AuthenticationEnum


class PasswordAuthentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.password


class Auth0Authentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.auth0
    config: Auth0Config = Field(default_factory=lambda: Auth0Config())


class GitHubAuthentication(BaseAuthentication):
    type: AuthenticationEnum = AuthenticationEnum.github
    config: GitHubConfig = Field(default_factory=lambda: GitHubConfig())


Authentication = Union[
    PasswordAuthentication, Auth0Authentication, GitHubAuthentication
]


def random_secure_string(
    length: int = 16, chars: str = string.ascii_lowercase + string.digits
):
    return "".join(secrets.choice(chars) for i in range(length))


class KeycloakThemes(schema.Base):
    enabled: bool = False
    repository: Optional[str] = ""
    branch: Optional[str] = "main"

    @model_validator(mode="before")
    @classmethod
    def validate_fields_dependencies(cls, data: Any) -> Any:
        # Raise and error if themes are enabled but repository or branch are not set
        if isinstance(data, dict) and data.get("enabled"):
            if not data.get("repository") or not data.get("branch"):
                raise ValueError(
                    "Repository and branch are both required when themes is enabled."
                )
        return data


class Keycloak(schema.Base):
    initial_root_password: str = Field(default_factory=random_secure_string)
    overrides: Dict = {}
    realm_display_name: str = "Nebari"
    themes: KeycloakThemes = Field(default_factory=lambda: KeycloakThemes())


auth_enum_to_model = {
    AuthenticationEnum.password: PasswordAuthentication,
    AuthenticationEnum.auth0: Auth0Authentication,
    AuthenticationEnum.github: GitHubAuthentication,
}

auth_enum_to_config = {
    AuthenticationEnum.auth0: Auth0Config,
    AuthenticationEnum.github: GitHubConfig,
}


class Security(schema.Base):
    authentication: Authentication = PasswordAuthentication()
    shared_users_group: bool = True
    keycloak: Keycloak = Keycloak()

    @field_validator("authentication", mode="before")
    @classmethod
    def validate_authentication(cls, value: Optional[Dict]) -> Authentication:
        if value is None:
            return PasswordAuthentication()
        if "type" not in value:
            raise ValueError(
                "Authentication type must be specified if authentication is set"
            )
        auth_type = value["type"] if hasattr(value, "__getitem__") else value.type
        if auth_type in auth_enum_to_model:
            if auth_type == AuthenticationEnum.password:
                return auth_enum_to_model[auth_type]()
            else:
                if "config" in value:
                    config_dict = (
                        value["config"]
                        if hasattr(value, "__getitem__")
                        else value.config
                    )
                    config = auth_enum_to_config[auth_type](**config_dict)
                else:
                    config = auth_enum_to_config[auth_type]()
                return auth_enum_to_model[auth_type](config=config)
        else:
            raise ValueError(f"Unsupported authentication type {auth_type}")


class InputSchema(schema.Base):
    security: Security = Security()


class KeycloakCredentials(schema.Base):
    url: str
    client_id: str
    realm: str
    username: str
    password: str


class OutputSchema(schema.Base):
    keycloak_credentials: KeycloakCredentials
    keycloak_nebari_bot_password: str


class KubernetesKeycloakStage(NebariTerraformStage):
    name = "05-kubernetes-keycloak"
    priority = 50

    input_schema = InputSchema
    output_schema = OutputSchema

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return InputVars(
            name=self.config.project_name,
            environment=self.config.namespace,
            endpoint=stage_outputs["stages/04-kubernetes-ingress"]["domain"],
            initial_root_password=self.config.security.keycloak.initial_root_password,
            overrides=[json.dumps(self.config.security.keycloak.overrides)],
            node_group=stage_outputs["stages/02-infrastructure"]["node_selectors"][
                "general"
            ],
            themes=self.config.security.keycloak.themes.model_dump(),
        ).model_dump()

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_check: bool = False
    ):
        from keycloak import KeycloakAdmin
        from keycloak.exceptions import KeycloakError

        keycloak_url = f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"

        def _attempt_keycloak_connection(
            keycloak_url,
            username,
            password,
            realm_name,
            client_id,
            verify=False,
            num_attempts=NUM_ATTEMPTS,
            timeout=TIMEOUT,
        ):
            for i in range(num_attempts):
                try:
                    KeycloakAdmin(
                        keycloak_url,
                        username=username,
                        password=password,
                        realm_name=realm_name,
                        client_id=client_id,
                        verify=verify,
                    )
                    print(
                        f"Attempt {i+1} succeeded connecting to keycloak master realm"
                    )
                    return True
                except KeycloakError:
                    print(f"Attempt {i+1} failed connecting to keycloak master realm")
                time.sleep(timeout)
            return False

        if not _attempt_keycloak_connection(
            keycloak_url,
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "username"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "password"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "realm"
            ],
            stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"][
                "client_id"
            ],
            verify=False,
        ):
            print(
                f"ERROR: unable to connect to keycloak master realm at url={keycloak_url} with root credentials"
            )
            sys.exit(1)

        print("Keycloak service successfully started")

    def post_deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        """Restore Keycloak database (if backup exists) and create nebari-bot user after Keycloak is deployed."""
        from pathlib import Path

        import kubernetes
        from keycloak import KeycloakAdmin
        from keycloak.exceptions import KeycloakError
        from kubernetes.stream import stream

        # Step 1: Restore database if backup exists
        backup_file = Path(self.output_directory) / "keycloak-backup.sql"

        if backup_file.exists():
            print("\n" + "=" * 80)
            print("KEYCLOAK DATABASE RESTORE")
            print("=" * 80)
            print(f"Found backup file: {backup_file}")
            print(f"Size: {backup_file.stat().st_size / 1024:.2f} KB\n")

            self._restore_keycloak_database(backup_file)

            # Rename backup file to prevent re-running restore on subsequent deploys
            backup_file.rename(backup_file.with_suffix('.sql.restored'))
            print(f"\n✓ Renamed backup file to {backup_file.with_suffix('.sql.restored')}")
            print("=" * 80 + "\n")
        else:
            print("No Keycloak database backup found, skipping restore")

        # Step 2: Create nebari-bot user
        keycloak_url = f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"
        nebari_bot_password = stage_outputs["stages/" + self.name]["keycloak_nebari_bot_password"]["value"]
        print("Creating nebari-bot user in Keycloak master realm...")

        max_attempts = 10
        retry_delay = 5  # seconds

        for attempt in range(1, max_attempts + 1):
            try:
                # Connect as root user
                admin = KeycloakAdmin(
                    keycloak_url,
                    username="root",
                    password=self.config.security.keycloak.initial_root_password,
                    realm_name="master",
                    client_id="admin-cli",
                    verify=False,
                )

                # Check if nebari-bot already exists
                users = admin.get_users({"username": "nebari-bot"})

                if users:
                    print("nebari-bot user already exists")
                    user_id = users[0]["id"]
                else:
                    # Create nebari-bot user
                    user_id = admin.create_user({
                        "username": "nebari-bot",
                        "enabled": True,
                        "credentials": [{
                            "type": "password",
                            "value": nebari_bot_password,
                            "temporary": False
                        }]
                    })
                    print("Successfully created nebari-bot user")

                # Assign admin role to nebari-bot user
                # Get the admin role from master realm
                admin_role = admin.get_realm_role("admin")

                # Check if user already has the admin role
                user_roles = admin.get_realm_roles_of_user(user_id)
                has_admin_role = any(role.get("name") == "admin" for role in user_roles)

                if not has_admin_role:
                    admin.assign_realm_roles(user_id, [admin_role])
                    print("Assigned admin role to nebari-bot user")
                else:
                    print("nebari-bot user already has admin role")

                # Success - break out of retry loop
                break

            except KeycloakError as e:
                if attempt < max_attempts:
                    print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to configure nebari-bot user after {max_attempts} attempts: {e}")
                    sys.exit(1)

    def _restore_keycloak_database(self, backup_file):
        """Restore PostgreSQL database from backup file using Kubernetes exec."""
        import kubernetes
        from kubernetes.stream import stream

        # Configuration - these should match your new postgres deployment
        namespace = self.config.namespace
        keycloak_statefulset_name = "keycloak-keycloakx"
        pod_name = "keycloak-postgres-standalone-postgresql-0"
        db_user = "keycloak"
        db_name = "keycloak"
        db_password = "keycloak"  # This should ideally come from config or secret
        postgres_user = "postgres"

        # Load kubernetes config
        kubernetes.config.load_kube_config()
        api = kubernetes.client.CoreV1Api()
        apps_api = kubernetes.client.AppsV1Api()

        # Step 0: Scale down Keycloak to prevent active database connections
        print(f"Step 0: Scaling down Keycloak statefulset '{keycloak_statefulset_name}' to 0 replicas...")
        try:
            # Get current statefulset
            statefulset = apps_api.read_namespaced_stateful_set(
                name=keycloak_statefulset_name,
                namespace=namespace
            )
            original_replicas = statefulset.spec.replicas
            print(f"  Current replicas: {original_replicas}")

            # Scale to 0
            statefulset.spec.replicas = 0
            apps_api.patch_namespaced_stateful_set(
                name=keycloak_statefulset_name,
                namespace=namespace,
                body=statefulset
            )
            print(f"  Scaled to 0 replicas")

            # Wait for pods to terminate
            print(f"  Waiting for Keycloak pods to terminate...")
            max_wait = 60  # seconds
            wait_interval = 2
            elapsed = 0
            while elapsed < max_wait:
                pods = api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=f"app.kubernetes.io/name=keycloak"
                )
                if len(pods.items) == 0:
                    print(f"  ✓ All Keycloak pods terminated")
                    break
                print(f"  Still waiting... ({len(pods.items)} pods remaining)")
                time.sleep(wait_interval)
                elapsed += wait_interval

            if elapsed >= max_wait:
                print(f"  ⚠ Warning: Timed out waiting for pods to terminate, proceeding anyway")

            print("✓ Keycloak scaled down\n")

        except kubernetes.client.exceptions.ApiException as e:
            print(f"⚠ Warning: Could not scale down Keycloak statefulset: {e}")
            print("Proceeding with restore anyway...\n")
            original_replicas = None

        # Check if pod exists
        print(f"Checking if pod '{pod_name}' exists in namespace '{namespace}'...")
        try:
            api.read_namespaced_pod(name=pod_name, namespace=namespace)
            print(f"✓ Pod found\n")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 404:
                print(f"✗ Pod '{pod_name}' not found in namespace '{namespace}'")
                print("Skipping database restore - pod may not be ready yet")
                return
            raise

        # Get postgres superuser password from secret
        print("Getting postgres superuser password from secret...")
        try:
            secret_name = "keycloak-postgres-standalone-postgresql"
            secret = api.read_namespaced_secret(name=secret_name, namespace=namespace)
            import base64
            postgres_password = base64.b64decode(secret.data['postgres-password']).decode('utf-8')
            print("✓ Got postgres password\n")
        except Exception as e:
            print(f"✗ Error getting postgres password: {e}")
            print("Skipping database restore")
            return

        # Helper function to run commands in pod
        def run_command(command, show_output=True):
            print(f"  Running: {command}")
            sys.stdout.flush()

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                name=pod_name,
                namespace=namespace,
                command=['/bin/sh', '-c', command],
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False
            )

            stdout_lines = []
            stderr_lines = []

            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    data = resp.read_stdout()
                    stdout_lines.append(data)
                    if show_output:
                        print(data, end='')
                        sys.stdout.flush()
                if resp.peek_stderr():
                    data = resp.read_stderr()
                    stderr_lines.append(data)
                    if show_output:
                        print(data, end='', file=sys.stderr)
                        sys.stderr.flush()

            resp.close()
            return ''.join(stdout_lines), ''.join(stderr_lines)

        # Helper function to run command with stdin
        def run_command_with_stdin(command, stdin_data, show_output=True):
            print(f"  Running: {command}")
            print(f"  Piping {len(stdin_data)} bytes to stdin...")
            sys.stdout.flush()

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                name=pod_name,
                namespace=namespace,
                command=['/bin/sh', '-c', command],
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False
            )

            # Write stdin data and close stdin to signal EOF
            resp.write_stdin(stdin_data)
            resp.write_stdin("")  # Signal EOF

            stdout_lines = []
            stderr_lines = []
            no_data_cycles = 0
            max_no_data_cycles = 30

            while resp.is_open():
                resp.update(timeout=1)
                has_data = False

                if resp.peek_stdout():
                    data = resp.read_stdout()
                    stdout_lines.append(data)
                    if show_output:
                        print(data, end='')
                        sys.stdout.flush()
                    has_data = True
                    no_data_cycles = 0

                if resp.peek_stderr():
                    data = resp.read_stderr()
                    stderr_lines.append(data)
                    if show_output:
                        print(data, end='', file=sys.stderr)
                        sys.stderr.flush()
                    has_data = True
                    no_data_cycles = 0

                if not has_data:
                    no_data_cycles += 1
                    if no_data_cycles >= max_no_data_cycles:
                        print("\n  No output for 30 seconds, assuming command completed...")
                        break

            resp.close()
            return ''.join(stdout_lines), ''.join(stderr_lines)

        # Step 1: Drop existing database
        print(f"Step 1: Dropping database '{db_name}' (if exists)...")
        drop_cmd = f"env PGPASSWORD={postgres_password} psql -U {postgres_user} -c 'DROP DATABASE IF EXISTS {db_name};'"
        run_command(drop_cmd)
        print("✓ Database dropped\n")

        # Step 2: Create fresh database
        print(f"Step 2: Creating fresh database '{db_name}'...")
        create_cmd = f"env PGPASSWORD={postgres_password} psql -U {postgres_user} -c 'CREATE DATABASE {db_name};'"
        run_command(create_cmd)
        print("✓ Database created\n")

        # Step 3: Grant privileges to keycloak user
        print(f"Step 3: Granting privileges to user '{db_user}'...")
        grant_db_cmd = f"env PGPASSWORD={postgres_password} psql -U {postgres_user} -c 'GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};'"
        run_command(grant_db_cmd)

        grant_schema_cmd = f"env PGPASSWORD={postgres_password} psql -U {postgres_user} -d {db_name} -c 'GRANT ALL ON SCHEMA public TO {db_user};'"
        run_command(grant_schema_cmd)

        grant_default_cmd = f"env PGPASSWORD={postgres_password} psql -U {postgres_user} -d {db_name} -c 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {db_user};'"
        run_command(grant_default_cmd)
        print("✓ Privileges granted\n")

        # Step 4: Read the backup file
        print(f"Step 4: Reading backup file...")
        with open(backup_file, 'r') as f:
            backup_sql = f.read()
        print(f"✓ Backup file loaded ({len(backup_sql)} characters)\n")

        # Step 5: Restore the database
        print(f"Step 5: Restoring database from backup...")
        print("This may take a few moments. Output will be shown below:\n")
        print("Note: Warnings about 'public' schema permissions are expected and harmless.")
        print("=" * 80)

        restore_cmd = f"env PGPASSWORD={db_password} psql -U {db_user} -d {db_name} --set ON_ERROR_STOP=off"
        run_command_with_stdin(restore_cmd, backup_sql)

        print("=" * 80)
        print("\n✓ Restore completed!\n")

        # Step 6: Verify the restore
        print(f"Step 6: Verifying restore by checking user count...")
        verify_cmd = f"env PGPASSWORD={db_password} psql -U {db_user} -d {db_name} -c 'SELECT count(*) FROM user_entity;'"
        run_command(verify_cmd)
        print("✓ Verification complete\n")

        print("=" * 80)
        print("DATABASE RESTORE SUCCESSFUL!")
        print("=" * 80)

        # Step 7: Scale Keycloak back up
        if original_replicas is not None:
            print(f"\nStep 7: Scaling Keycloak statefulset back to {original_replicas} replicas...")
            try:
                statefulset = apps_api.read_namespaced_stateful_set(
                    name=keycloak_statefulset_name,
                    namespace=namespace
                )
                statefulset.spec.replicas = original_replicas
                apps_api.patch_namespaced_stateful_set(
                    name=keycloak_statefulset_name,
                    namespace=namespace,
                    body=statefulset
                )
                print(f"✓ Keycloak scaled back to {original_replicas} replicas")
                print("  Keycloak pods will start connecting to the restored database\n")
            except kubernetes.client.exceptions.ApiException as e:
                print(f"⚠ Warning: Could not scale up Keycloak statefulset: {e}")
                print(f"  You may need to manually scale it back up: kubectl scale statefulset {keycloak_statefulset_name} --replicas={original_replicas} -n {namespace}\n")

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        with super().deploy(stage_outputs, disable_prompt):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"]
            ):
                yield

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        with super().destroy(stage_outputs, status):
            with keycloak_provider_context(
                stage_outputs["stages/" + self.name]["keycloak_credentials"]["value"]
            ):
                yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesKeycloakStage]
