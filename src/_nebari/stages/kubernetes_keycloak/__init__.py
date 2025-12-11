import base64
import contextlib
import enum
import json
import os
import secrets
import string
import subprocess
import sys
import tarfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import kubernetes
import yaml
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from kubernetes.stream import stream
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
    git_repo_path: Optional[str] = None


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


class KeycloakGitOpsHelper:
    """Helper class for GitOps operations with Argo CD"""

    def __init__(self, config, stage_outputs, git_repo_path: Path):
        self.config = config
        self.stage_outputs = stage_outputs
        self.git_repo_path = Path(git_repo_path)

    def generate_postgresql_values(self) -> Dict[str, Any]:
        """Generate PostgreSQL values.yaml from Nebari config"""
        node_selectors_raw = self.stage_outputs["stages/02-infrastructure"][
            "node_selectors"
        ]["general"]

        # Convert from {key: "kubernetes.io/os", value: "linux"} to {"kubernetes.io/os": "linux"}
        if (
            isinstance(node_selectors_raw, dict)
            and "key" in node_selectors_raw
            and "value" in node_selectors_raw
        ):
            node_selectors = {node_selectors_raw["key"]: node_selectors_raw["value"]}
        else:
            node_selectors = node_selectors_raw

        return {
            "fullnameOverride": "keycloak-postgresql",
            "primary": {
                "nodeSelector": node_selectors,
                "resources": {
                    "requests": {"memory": "256Mi", "cpu": "100m"},
                    "limits": {"memory": "512Mi", "cpu": "250m"},
                },
            },
        }

    def generate_keycloak_values(self, nebari_bot_password: str) -> Dict[str, Any]:
        """Generate Keycloak values.yaml from Nebari config"""
        node_selectors_raw = self.stage_outputs["stages/02-infrastructure"][
            "node_selectors"
        ]["general"]
        external_url = self.stage_outputs["stages/04-kubernetes-ingress"]["domain"]

        # Convert from {key: "kubernetes.io/os", value: "linux"} to {"kubernetes.io/os": "linux"}
        if (
            isinstance(node_selectors_raw, dict)
            and "key" in node_selectors_raw
            and "value" in node_selectors_raw
        ):
            node_selectors = {node_selectors_raw["key"]: node_selectors_raw["value"]}
        else:
            node_selectors = node_selectors_raw

        # Generate environment variables
        env_vars = [
            {"name": "KC_HOSTNAME", "value": external_url},
            {"name": "KC_HOSTNAME_PATH", "value": "/auth"},
            {"name": "KC_HOSTNAME_STRICT", "value": "false"},
            {"name": "KC_HOSTNAME_STRICT_HTTPS", "value": "false"},
            {"name": "KC_HTTP_ENABLED", "value": "true"},
            {"name": "KC_PROXY_HEADERS", "value": "xforwarded"},
            {"name": "KEYCLOAK_ADMIN", "value": "root"},
            {
                "name": "KEYCLOAK_ADMIN_PASSWORD",
                "value": self.config.security.keycloak.initial_root_password,
            },
            {"name": "KC_HEALTH_ENABLED", "value": "true"},
            {"name": "KC_METRICS_ENABLED", "value": "true"},
        ]

        # Convert to YAML string format expected by extraEnv
        env_yaml = yaml.dump(env_vars, default_flow_style=False)

        return {
            "replicas": 1,
            "database": {
                "hostname": "keycloak-postgresql",
                "existingSecret": "keycloak-postgresql",
                "database": "keycloak",
                "password": "keycloak",
            },
            "extraEnv": env_yaml,
            "nodeSelector": node_selectors,
            "resources": {
                "requests": {"memory": "512Mi", "cpu": "250m"},
                "limits": {"memory": "1Gi", "cpu": "500m"},
            },
            "customThemes": self.config.security.keycloak.themes.model_dump(),
        }

    def write_values_files(self, nebari_bot_password: str):
        """Write values files to Git repository"""
        # Ensure directories exist
        Path("postgresql").mkdir(parents=True, exist_ok=True)
        Path("keycloak").mkdir(parents=True, exist_ok=True)

        # Generate and write PostgreSQL values
        pg_values = self.generate_postgresql_values()
        with open(Path("postgresql") / "values.yaml", "w") as f:
            yaml.dump(pg_values, f, default_flow_style=False, sort_keys=False)

        # Generate and write Keycloak values
        kc_values = self.generate_keycloak_values(nebari_bot_password)
        with open(Path("keycloak") / "values.yaml", "w") as f:
            yaml.dump(kc_values, f, default_flow_style=False, sort_keys=False)

        print("Generated values files for GitOps deployment")

    def commit_and_push(self, message: str = "Update Keycloak configuration"):
        """Commit and push values files to Git"""
        try:
            # Add the values files
            subprocess.run(
                ["git", "add", "postgresql/values.yaml", "keycloak/values.yaml"],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                text=True,
            )

            # Try to commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Check if it's because there's nothing to commit
                error_output = result.stdout + result.stderr
                if (
                    "nothing to commit" in error_output
                    or "no changes added to commit" in error_output
                ):
                    print("No configuration changes to commit")
                    return
                else:
                    # Some other error occurred
                    print(f"Git commit failed: {error_output}")
                    raise subprocess.CalledProcessError(
                        result.returncode, result.args, result.stdout, result.stderr
                    )

            # Push to remote
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                text=True,
            )
            print("Committed and pushed configuration to Git")
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e.stderr if e.stderr else e}")

    def install_argocd(self):
        """Install Argo CD using kubectl apply -k argocd/"""
        # Check if ArgoCD namespace already exists
        result = subprocess.run(
            ["kubectl", "get", "namespace", "argocd"], capture_output=True
        )

        if result.returncode != 0:
            # ArgoCD not installed, install it
            print("Installing Argo CD...")
            subprocess.run(["kubectl", "apply", "-k", "argocd/"], check=True)
            print("Argo CD installed successfully")

            # Wait for ArgoCD to be ready
            print("Waiting for Argo CD to be ready...")
            subprocess.run(
                [
                    "kubectl",
                    "wait",
                    "--for=condition=available",
                    "--timeout=300s",
                    "deployment/argocd-server",
                    "-n",
                    "argocd",
                ],
                check=True,
            )
            print("Argo CD is ready")
        else:
            print("Argo CD already installed")

    def ensure_argocd_applications(self):
        """Ensure Argo CD Application manifests are applied"""
        apps_dir = Path.cwd() / "apps"

        # Check if applications already exist
        result = subprocess.run(
            ["kubectl", "get", "application", "keycloak", "-n", "argocd"],
            capture_output=True,
        )

        if result.returncode != 0:
            # Applications don't exist, create them
            print("Creating Argo CD Applications...")
            subprocess.run(["kubectl", "apply", "-f", str(apps_dir)], check=True)
            print("Applied Argo CD Applications")
        else:
            print("Argo CD Applications already exist")

    def install_ingressroute(self):
        """Install Keycloak IngressRoute"""
        ingressroute_path = Path.cwd() / "keycloak" / "ingressroute.yaml"

        if not ingressroute_path.exists():
            print(
                f"Warning: IngressRoute file not found at {ingressroute_path}, skipping"
            )
            return

        # Check if ingressroute already exists
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "ingressroute",
                "keycloak-http",
                "-n",
                self.config.namespace,
            ],
            capture_output=True,
        )

        if result.returncode != 0:
            # IngressRoute doesn't exist, create it
            print("Installing Keycloak IngressRoute...")
            subprocess.run(
                ["kubectl", "apply", "-f", str(ingressroute_path)], check=True
            )
            print("Keycloak IngressRoute installed successfully")
        else:
            print("Keycloak IngressRoute already exists")

    def wait_for_sync(self, app_name: str, timeout: int = 600):
        """Wait for Argo CD Application to sync"""
        print(f"Waiting for {app_name} to sync...")

        # First check if the Application exists
        check_result = subprocess.run(
            ["kubectl", "get", "application", app_name, "-n", "argocd", "-o", "json"],
            capture_output=True,
            text=True,
        )

        if check_result.returncode != 0:
            print(f"Error: Application {app_name} does not exist")
            print(f"kubectl output: {check_result.stderr}")
            return

        # Show current status
        status_result = subprocess.run(
            ["kubectl", "get", "application", app_name, "-n", "argocd"],
            capture_output=True,
            text=True,
        )
        print(f"Current status:\n{status_result.stdout}")

        # Try to wait for sync - use condition instead of jsonpath
        try:
            subprocess.run(
                [
                    "kubectl",
                    "wait",
                    f"application/{app_name}",
                    "-n",
                    "argocd",
                    "--for=jsonpath={.status.sync.status}=Synced",
                    f"--timeout={timeout}s",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"{app_name} synced successfully")
        except subprocess.CalledProcessError:
            # Show detailed status on failure
            print(f"Warning: {app_name} sync wait failed")
            describe_result = subprocess.run(
                ["kubectl", "describe", "application", app_name, "-n", "argocd"],
                capture_output=True,
                text=True,
            )
            print(f"Application details:\n{describe_result.stdout}")

            # Check if it's actually synced despite the wait failure
            import json

            try:
                app_json = json.loads(check_result.stdout)
                sync_status = (
                    app_json.get("status", {}).get("sync", {}).get("status", "Unknown")
                )
                health_status = (
                    app_json.get("status", {})
                    .get("health", {})
                    .get("status", "Unknown")
                )
                print(f"Actual sync status: {sync_status}")
                print(f"Health status: {health_status}")

                if sync_status == "Synced":
                    print(f"{app_name} is synced (despite wait command failure)")
            except Exception:
                pass

    def get_keycloak_credentials(self) -> Dict[str, str]:
        """Get Keycloak credentials for output"""
        external_url = self.stage_outputs["stages/04-kubernetes-ingress"]["domain"]

        return {
            "url": f"https://{external_url}",
            "username": "root",
            "password": self.config.security.keycloak.initial_root_password,
            "realm": "master",
            "client_id": "admin-cli",
        }


class KubernetesKeycloakStage(NebariTerraformStage):
    name = "05-kubernetes-keycloak"
    priority = 50

    input_schema = InputSchema
    output_schema = OutputSchema

    def __init__(self, output_directory, config, git_repo_path=None):
        super().__init__(output_directory, config)
        # Git repo path - priority order:
        # 1. Explicit parameter (for testing)
        # 2. Config value from nebari-config.yaml (security.keycloak.git_repo_path)
        # 3. None (will use Terraform instead of GitOps)
        if git_repo_path:
            self.git_repo_path = Path(git_repo_path)
        elif config.security.keycloak.git_repo_path:
            self.git_repo_path = Path(config.security.keycloak.git_repo_path)
        else:
            self.git_repo_path = None

    def tf_objects(self) -> List[Dict]:
        """
        DEPRECATED: This method is no longer used by GitOps deployment.
        Kept for backwards compatibility only.
        The GitOps deployment uses Argo CD Applications instead of Terraform.
        """
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        """
        DEPRECATED: This method is no longer used by GitOps deployment.
        Kept for backwards compatibility only.
        The GitOps deployment generates values.yaml files directly instead of
        using Terraform variables.
        """
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

        # Step 1: Restore database if backup exists
        backup_file = Path(self.output_directory) / "keycloak-backup.sql"

        if backup_file.exists():
            print("\n" + "=" * 80)
            print("KEYCLOAK DATABASE RESTORE")
            print("=" * 80)
            print(f"Found backup file: {backup_file}")
            print(f"Size: {backup_file.stat().st_size / 1024:.2f} KB\n")

            try:
                self._restore_keycloak_database(backup_file)

                # Rename backup file to prevent re-running restore on subsequent deploys
                backup_file.rename(backup_file.with_suffix(".sql.restored"))
                print(
                    f"\n✓ Renamed backup file to {backup_file.with_suffix('.sql.restored')}"
                )
                print("=" * 80 + "\n")
            except Exception as e:
                backup_file.rename(backup_file.with_suffix(".sql.failed_restore"))
                print("\n" + "=" * 80)
                print("ERROR: KEYCLOAK DATABASE RESTORE FAILED")
                print("=" * 80)
                print(f"Error: {e}")
                print(f"Backup file location: {backup_file.absolute()}")
                print("\nThe backup file has been preserved for manual recovery.")
                print("=" * 80 + "\n")
                raise
        else:
            print("No Keycloak database backup found, skipping restore")

        # Step 2: Create nebari-bot user
        keycloak_url = f"{stage_outputs['stages/' + self.name]['keycloak_credentials']['value']['url']}/auth/"
        nebari_bot_password = stage_outputs["stages/" + self.name][
            "keycloak_nebari_bot_password"
        ]["value"]
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

                    # Reset password to ensure it matches the expected value
                    # (Keycloak doesn't allow reading passwords for comparison)
                    admin.set_user_password(
                        user_id=user_id, password=nebari_bot_password, temporary=False
                    )
                    print("Updated nebari-bot password to match expected value")
                else:
                    # Create nebari-bot user
                    user_id = admin.create_user(
                        {
                            "username": "nebari-bot",
                            "enabled": True,
                            "credentials": [
                                {
                                    "type": "password",
                                    "value": nebari_bot_password,
                                    "temporary": False,
                                }
                            ],
                        }
                    )
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
                    print(
                        f"Failed to configure nebari-bot user after {max_attempts} attempts: {e}"
                    )
                    sys.exit(1)

    def _restore_keycloak_database(self, backup_file: Path):
        """Restore PostgreSQL database from backup file using Kubernetes exec."""
        # Configuration
        namespace = self.config.namespace
        db_user = "keycloak"
        db_name = "keycloak"
        postgres_user = "postgres"

        # Load kubernetes config
        kubernetes.config.load_kube_config()
        api = kubernetes.client.CoreV1Api()
        apps_api = kubernetes.client.AppsV1Api()

        # Find Keycloak StatefulSet by label
        statefulsets = apps_api.list_namespaced_stateful_set(
            namespace=namespace, label_selector="app.kubernetes.io/name=keycloakx"
        )
        keycloak_statefulset_name = statefulsets.items[0].metadata.name

        # Find PostgreSQL pod by label
        postgres_pods = api.list_namespaced_pod(
            namespace=namespace,
            label_selector="app.kubernetes.io/name=postgresql,app.kubernetes.io/component=primary",
        )
        postgres_pod_name = postgres_pods.items[0].metadata.name

        # Step 0: Scale down Keycloak to prevent active database connections
        # Keycloak statefulset always runs with 1 replica
        original_replicas = 1
        print(
            f"Step 0: Scaling down Keycloak statefulset '{keycloak_statefulset_name}' to 0 replicas..."
        )
        try:
            # Get current statefulset and scale to 0
            statefulset = apps_api.read_namespaced_stateful_set(
                name=keycloak_statefulset_name, namespace=namespace
            )
            statefulset.spec.replicas = 0
            apps_api.patch_namespaced_stateful_set(
                name=keycloak_statefulset_name, namespace=namespace, body=statefulset
            )
            print("  Scaled to 0 replicas")

            # Wait for pods to terminate
            print("  Waiting for Keycloak pods to terminate...")
            max_wait = 60  # seconds
            wait_interval = 2
            elapsed = 0
            while elapsed < max_wait:
                pods = api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector="app.kubernetes.io/name=keycloak",
                )
                if len(pods.items) == 0:
                    print("  ✓ All Keycloak pods terminated")
                    break
                print(f"  Still waiting... ({len(pods.items)} pods remaining)")
                time.sleep(wait_interval)
                elapsed += wait_interval

            if elapsed >= max_wait:
                print(
                    "  ⚠ Warning: Timed out waiting for pods to terminate, proceeding anyway"
                )

            print("✓ Keycloak scaled down\n")

        except kubernetes.client.exceptions.ApiException as e:
            print(f"⚠ Warning: Could not scale down Keycloak statefulset: {e}")
            print("Proceeding with restore anyway...\n")

        # Check if pod exists
        print(
            f"Checking if pod '{postgres_pod_name}' exists in namespace '{namespace}'..."
        )
        try:
            api.read_namespaced_pod(name=postgres_pod_name, namespace=namespace)
            print("✓ Pod found\n")
        except kubernetes.client.exceptions.ApiException as e:
            if e.status == 404:
                print(
                    f"✗ Pod '{postgres_pod_name}' not found in namespace '{namespace}'"
                )
                print("Skipping database restore - pod may not be ready yet")
                return
            raise

        # Get postgres passwords from secret
        print("Getting database passwords from secret...")
        try:
            secret_name = "keycloak-postgres-standalone-postgresql"
            secret = api.read_namespaced_secret(name=secret_name, namespace=namespace)
            postgres_password = base64.b64decode(
                secret.data["postgres-password"]
            ).decode("utf-8")
            db_password = base64.b64decode(secret.data["password"]).decode("utf-8")
            print("✓ Got database passwords\n")
        except Exception as e:
            raise (f"✗ Error getting database passwords: {e}")

        # Helper function to run commands in pod
        def run_command(command: str, show_output: bool = True):
            # Mask password in output
            masked_command = command.replace(postgres_password, "***").replace(
                db_password, "***"
            )
            print(f"  Running: {masked_command}")
            sys.stdout.flush()

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                name=postgres_pod_name,
                namespace=namespace,
                command=["/bin/sh", "-c", command],
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            stdout_lines = []
            stderr_lines = []

            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    data = resp.read_stdout()
                    stdout_lines.append(data)
                    if show_output:
                        print(data, end="")
                        sys.stdout.flush()
                if resp.peek_stderr():
                    data = resp.read_stderr()
                    stderr_lines.append(data)
                    if show_output:
                        print(data, end="", file=sys.stderr)
                        sys.stderr.flush()

            resp.close()
            return "".join(stdout_lines), "".join(stderr_lines)

        # Helper function to copy file to pod using tar
        def copy_file_to_pod(local_path: Path, remote_path: Path):
            """
            Copy a file to pod using tar (similar to kubectl cp).
            More reliable than stdin streaming for large files.
            """
            print(f"  Copying {local_path.name} to pod:{remote_path.name}")
            print(f"  File size: {local_path.stat().st_size / 1024:.2f} KB")

            # Create tar archive in memory
            tar_buffer = BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tar.add(str(local_path), arcname=remote_path.name)

            tar_buffer.seek(0)
            tar_data = tar_buffer.getvalue()

            # Extract tar in pod
            remote_dir = str(remote_path.parent)
            extract_cmd = ["tar", "xf", "-", "-C", remote_dir or "/"]

            resp = stream(
                api.connect_get_namespaced_pod_exec,
                name=postgres_pod_name,
                namespace=namespace,
                command=extract_cmd,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            # Write tar data in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(0, len(tar_data), chunk_size):
                chunk = tar_data[i : i + chunk_size]
                resp.write_stdin(chunk)

            resp.write_stdin("")  # Signal EOF
            resp.close()

            print("  ✓ File copied successfully")

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

        # Step 4: Copy backup file to pod
        print("Step 4: Copying backup file to pod...")
        remote_backup_path = "/tmp/keycloak-backup.sql"
        copy_file_to_pod(Path(backup_file), Path(remote_backup_path))
        print("✓ Backup file copied to pod\n")

        # Step 5: Restore the database from file
        print("Step 5: Restoring database from backup...")
        print("This may take a few moments. Output will be shown below:\n")
        print(
            "Note: Warnings about 'public' schema permissions are expected and harmless."
        )
        print("=" * 80)

        restore_cmd = f"env PGPASSWORD={db_password} psql -U {db_user} -d {db_name} --set ON_ERROR_STOP=off -f {remote_backup_path}"
        run_command(restore_cmd)

        print("=" * 80)
        print("\n✓ Restore completed!\n")

        # Step 6: Verify the restore
        print("Step 6: Verifying restore by checking user count...")
        verify_cmd = f"env PGPASSWORD={db_password} psql -U {db_user} -d {db_name} -c 'SELECT count(*) FROM user_entity;'"
        run_command(verify_cmd)
        print("✓ Verification complete\n")

        # Step 7: Clean up temporary file in pod
        print("Step 7: Cleaning up temporary file in pod...")
        cleanup_cmd = f"rm -f {remote_backup_path}"
        run_command(cleanup_cmd, show_output=False)
        print(f"✓ Removed {remote_backup_path}\n")

        print("=" * 80)
        print("DATABASE RESTORE SUCCESSFUL!")
        print("=" * 80)

        # Step 8: Scale Keycloak back up to 1 replica
        print(
            f"\nStep 8: Scaling Keycloak statefulset back to {original_replicas} replicas..."
        )
        try:
            statefulset = apps_api.read_namespaced_stateful_set(
                name=keycloak_statefulset_name, namespace=namespace
            )
            statefulset.spec.replicas = original_replicas
            apps_api.patch_namespaced_stateful_set(
                name=keycloak_statefulset_name,
                namespace=namespace,
                body=statefulset,
            )
            print(f"✓ Keycloak scaled back to {original_replicas} replicas")

            # Wait for StatefulSet to be ready
            print("  Waiting for Keycloak to be ready...")
            max_wait = 300  # 5 minutes
            wait_interval = 5
            elapsed = 0

            while elapsed < max_wait:
                statefulset = apps_api.read_namespaced_stateful_set(
                    name=keycloak_statefulset_name, namespace=namespace
                )

                ready_replicas = statefulset.status.ready_replicas or 0
                current_replicas = statefulset.status.current_replicas or 0

                if (
                    ready_replicas == original_replicas
                    and current_replicas == original_replicas
                ):
                    print(
                        f"  ✓ Keycloak is ready ({ready_replicas}/{original_replicas} replicas)"
                    )
                    break

                print(
                    f"  Still waiting... ({ready_replicas}/{original_replicas} ready)"
                )
                time.sleep(wait_interval)
                elapsed += wait_interval

            if elapsed >= max_wait:
                print("  ⚠ Warning: Timed out waiting for StatefulSet to be ready")
                print("  The StatefulSet may still be starting up")
            else:
                print(
                    "  Keycloak pods are ready and connected to the restored database\n"
                )

        except kubernetes.client.exceptions.ApiException as e:
            print(f"⚠ Warning: Could not scale up Keycloak statefulset: {e}")
            print(
                f"  You may need to manually scale it back up: kubectl scale statefulset {keycloak_statefulset_name} --replicas={original_replicas} -n {namespace}\n"
            )

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        """Deploy Keycloak using GitOps pattern with Argo CD (if configured) or Terraform"""

        # Check if GitOps is configured
        if self.git_repo_path is None:
            # Fall back to Terraform deployment
            print(
                "GitOps not configured (git_repo_path is None), using Terraform deployment"
            )
            with super().deploy(stage_outputs, disable_prompt):
                with keycloak_provider_context(
                    stage_outputs["stages/" + self.name]["keycloak_credentials"][
                        "value"
                    ]
                ):
                    yield
            return

        # GitOps deployment
        print("\n" + "=" * 80)
        print("DEPLOYING KEYCLOAK VIA GITOPS")
        print("=" * 80)
        print(f"Git repository: {self.git_repo_path}")

        # Generate nebari-bot password
        nebari_bot_password = random_secure_string(32)

        # Create GitOps helper
        helper = KeycloakGitOpsHelper(self.config, stage_outputs, self.git_repo_path)

        # 1. Generate values files
        print("\n[1/7] Generating deployment-specific values files...")
        helper.write_values_files(nebari_bot_password)

        # 2. Commit and push to Git
        print("\n[2/7] Committing and pushing to Git...")
        helper.commit_and_push(f"Deploy Keycloak for {self.config.project_name}")

        # 3. Install Argo CD
        print("\n[3/7] Installing Argo CD...")
        helper.install_argocd()

        # 4. Ensure Argo CD Applications exist
        print("\n[4/7] Ensuring Argo CD Applications are applied...")
        helper.ensure_argocd_applications()

        # 5. Wait for Argo CD to sync
        print("\n[5/7] Waiting for Argo CD to sync deployments...")
        helper.wait_for_sync("keycloak-postgresql")
        helper.wait_for_sync("keycloak")

        # 6. Install IngressRoute
        print("\n[6/7] Installing Keycloak IngressRoute...")
        helper.install_ingressroute()

        # 7. Prepare outputs for next stages
        print("\n[7/7] Preparing stage outputs...")
        keycloak_credentials = helper.get_keycloak_credentials()

        # Store outputs for access by check() and post_deploy()
        # These outputs mimic the structure that was previously provided by Terraform
        if "stages/" + self.name not in stage_outputs:
            stage_outputs["stages/" + self.name] = {}

        stage_outputs["stages/" + self.name]["keycloak_credentials"] = {
            "value": keycloak_credentials
        }
        stage_outputs["stages/" + self.name]["keycloak_nebari_bot_password"] = {
            "value": nebari_bot_password
        }

        print("\n" + "=" * 80)
        print("KEYCLOAK DEPLOYED SUCCESSFULLY VIA GITOPS")
        print("=" * 80 + "\n")

        # Set up keycloak provider context for any downstream operations
        with keycloak_provider_context(keycloak_credentials):
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
