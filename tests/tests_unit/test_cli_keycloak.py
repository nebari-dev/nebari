import ast
import json
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Any, List
from unittest.mock import Mock, patch

import keycloak.exceptions
import pytest
import requests.exceptions
import yaml
from typer.testing import CliRunner

from _nebari.cli import create_cli
from _nebari.keycloak import get_expected_roles

TEST_KEYCLOAK_USERS = [
    {"id": "1", "username": "test-dev", "groups": ["analyst", "developer"]},
    {"id": "2", "username": "test-admin", "groups": ["admin"]},
    {"id": "3", "username": "test-nogroup", "groups": []},
]

TEST_KEYCLOAK_GROUPS = [
    {"name": "admin", "path": "/admin"},
    {"name": "analyst", "path": "/analyst"},
    {"name": "developer", "path": "/developer"},
    {"name": "superadmin", "path": "/superadmin"},
    {"name": "users", "path": "/users"},
]

TEST_KEYCLOAK_GROUP_CLIENT_ROLES = {
    "/admin": {
        "realm-management": ["query-users", "query-groups", "manage-users"],
        "jupyterhub": [
            "jupyterhub_admin",
            "dask_gateway_admin",
            "allow-group-directory-creation-role",
        ],
        "grafana": ["grafana_admin"],
        "argo-server-sso": ["argo-admin"],
        "conda_store": ["conda_store_admin"],
    },
    "/analyst": {
        "jupyterhub": [
            "jupyterhub_developer",
            "allow-group-directory-creation-role",
            "allow-read-access-to-services-role",
        ],
        "grafana": ["grafana_viewer"],
        "argo-server-sso": ["argo-viewer"],
        "conda_store": ["conda_store_developer"],
    },
    "/developer": {
        "jupyterhub": [
            "jupyterhub_developer",
            "allow-group-directory-creation-role",
            "dask_gateway_developer",
        ],
        "grafana": ["grafana_developer"],
        "argo-server-sso": ["argo-developer"],
        "conda_store": ["conda_store_developer"],
    },
    "/superadmin": {
        "realm-management": ["realm-admin"],
        "conda_store": ["conda_store_superadmin"],
    },
    "/users": {},
}


TEST_DOMAIN = "nebari.example.com"
MOCK_KEYCLOAK_ENV = {
    "KEYCLOAK_SERVER_URL": f"https://{TEST_DOMAIN}/auth/",
    "KEYCLOAK_ADMIN_USERNAME": "root",
    "KEYCLOAK_ADMIN_PASSWORD": "super-secret-123!",
}

TEST_ACCESS_TOKEN = "abc123"

runner = CliRunner()


def parse_table(table_text, headers: list):
    """
    A simple parser that extracts the rows from your table into a list of tuples/dicts.
    Assumes that each row is in the format and order of the headers list.
    """
    rows = []
    # Split by lines and filter out lines that don't have '│' columns
    for line in table_text.splitlines():
        if line.strip().startswith("│"):
            # Example split by '│', ignoring first and last segments
            columns = [col.strip() for col in line.split("│")[1:-1]]
            if len(columns) == len(headers):
                rows.append(dict(zip(headers, columns)))
    return rows


def parse_yaml(stdout_str: str, headers: list):
    """
    A simple parser that extracts the rows from your YAML into a list of dicts.
    Assumes your YAML is a list of objects, and each object might contain fields
    corresponding to the given headers list.
    """
    # Use yaml.safe_load to parse the YAML string into Python data
    data = yaml.safe_load(stdout_str)

    # If the YAML is empty or not a list, ensure we handle gracefully
    if not data or not isinstance(data, list):
        return []

    parsed_rows = []

    # Loop over each object in the YAML list
    for item in data:
        # Build a new dict containing only the desired headers in the specified order
        row = {}
        for h in headers:
            row[h] = item.get(h, None)  # or some default if the key is missing
        parsed_rows.append(row)

    return parsed_rows


def test_parse_table():
    table_str = dedent(
        """                      Keycloak Users (Count: 3)
        ┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Username     ┃ Email                    ┃ Groups                   ┃
        ┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
        │ test-dev     │ test-dev@example.com     │ ['analyst', 'developer'] │
        │ test-admin   │ test-admin@example.com   │ ['admin']                │
        │ test-nogroup │ test-nogroup@example.com │ []                       │
        └──────────────┴──────────────────────────┴──────────────────────────┘
        """
    )
    expected = [
        {
            "username": "test-dev",
            "email": "test-dev@example.com",
            "groups": "['analyst', 'developer']",
        },
        {
            "username": "test-admin",
            "email": "test-admin@example.com",
            "groups": "['admin']",
        },
        {
            "username": "test-nogroup",
            "email": "test-nogroup@example.com",
            "groups": "[]",
        },
    ]
    parsed_result = parse_table(table_str, ["username", "email", "groups"])
    print(parsed_result)
    assert 3 == len(parsed_result)
    for i, row in enumerate(parsed_result):
        assert expected[i] == row


def test_parse_yaml():
    yaml_str = dedent(
        """
        - name: test
          roles:
            - allow-test-to-pass
            - other-role
        """
    )
    expected = [
        {
            "name": "test",
            "roles": ["allow-test-to-pass", "other-role"],
        },
    ]

    parsed_result = parse_yaml(yaml_str, ["name", "roles"])
    print(parsed_result)
    assert 1 == len(parsed_result)
    assert expected[0] == parsed_result[0]


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        ([], 0, ["Usage:"]),
        (["--help"], 0, ["Usage:"]),
        (["-h"], 0, ["Usage:"]),
        (["add-user", "--help"], 0, ["Usage:"]),
        (["add-user", "-h"], 0, ["Usage:"]),
        (["export-users", "--help"], 0, ["Usage:"]),
        (["export-users", "-h"], 0, ["Usage:"]),
        (["list-users", "--help"], 0, ["Usage:"]),
        (["list-users", "-h"], 0, ["Usage:"]),
        (["list-groups", "--help"], 0, ["Usage:"]),
        (["list-groups", "-h"], 0, ["Usage:"]),
        # error, missing args
        (["add-user"], 2, ["Missing option"]),
        (["add-user", "--config"], 2, ["requires an argument"]),
        (["add-user", "-c"], 2, ["requires an argument"]),
        (["add-user", "--user"], 2, ["requires an argument"]),
        (["export-users"], 2, ["Missing option"]),
        (["export-users", "--config"], 2, ["requires an argument"]),
        (["export-users", "-c"], 2, ["requires an argument"]),
        (["export-users", "--realm"], 2, ["requires an argument"]),
        (["list-users"], 2, ["Missing option"]),
        (["list-users", "--config"], 2, ["requires an argument"]),
        (["list-users", "-c"], 2, ["requires an argument"]),
        (["list-groups"], 2, ["Missing option"]),
        (["list-groups", "--config"], 2, ["requires an argument"]),
        (["list-groups", "-c"], 2, ["requires an argument"]),
    ],
)
def test_cli_keycloak_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["keycloak"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


@patch("keycloak.KeycloakAdmin")
def test_cli_keycloak_adduser_happy_path_from_env(_mock_keycloak_admin):
    result = run_cli_keycloak_adduser(use_env=True)

    assert 0 == result.exit_code
    assert not result.exception
    assert f"Created user={TEST_KEYCLOAK_USERS[0]['username']}" in result.stdout


@patch("keycloak.KeycloakAdmin")
def test_cli_keycloak_adduser_happy_path_from_config(_mock_keycloak_admin):
    result = run_cli_keycloak_adduser(use_env=False)

    assert 0 == result.exit_code
    assert not result.exception
    assert f"Created user={TEST_KEYCLOAK_USERS[0]['username']}" in result.stdout


@patch(
    "keycloak.KeycloakAdmin.__init__",
    side_effect=keycloak.exceptions.KeycloakConnectionError(
        error_message="connection test"
    ),
)
def test_cli_keycloak_adduser_keycloak_connection_exception(_mock_keycloak_admin):
    result = run_cli_keycloak_adduser()

    assert 1 == result.exit_code
    assert result.exception
    assert "Failed to connect to Keycloak server: connection test" in str(
        result.exception
    )


@patch(
    "keycloak.KeycloakAdmin.__init__",
    side_effect=keycloak.exceptions.KeycloakAuthenticationError(
        error_message="auth test"
    ),
)
def test_cli_keycloak_adduser_keycloak_auth_exception(_mock_keycloak_admin):
    result = run_cli_keycloak_adduser()

    assert 1 == result.exit_code
    assert result.exception
    assert "Failed to connect to Keycloak server: auth test" in str(result.exception)


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        create_user=Mock(
            side_effect=keycloak.exceptions.KeycloakConnectionError(
                error_message="unhandled"
            )
        ),
    ),
)
def test_cli_keycloak_adduser_keycloak_unhandled_error(_mock_keycloak_admin):
    result = run_cli_keycloak_adduser()

    assert 1 == result.exit_code
    assert result.exception
    assert "unhandled" == str(result.exception)


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        users_count=Mock(side_effect=lambda: len(TEST_KEYCLOAK_USERS)),
        get_users=Mock(
            side_effect=lambda: [
                {
                    "id": u["id"],
                    "username": u["username"],
                    "email": f"{u['username']}@example.com",
                }
                for u in TEST_KEYCLOAK_USERS
            ]
        ),
        get_user_groups=Mock(
            side_effect=lambda user_id: [
                {"name": g}
                for u in TEST_KEYCLOAK_USERS
                if u["id"] == user_id
                for g in u["groups"]
            ]
        ),
    ),
)
def test_cli_keycloak_listusers_happy_path_from_env(_mock_keycloak_admin):
    result = run_cli_keycloak_listusers(use_env=True)

    assert 0 == result.exit_code
    assert not result.exception

    parsed_result = parse_table(result.stdout, ["username", "email", "groups"])

    # output should start with the number of users found then
    # display a table with their info
    assert len(TEST_KEYCLOAK_USERS) == len(parsed_result)

    for i, u in enumerate(TEST_KEYCLOAK_USERS):
        assert u["username"] == parsed_result[i]["username"]
        assert f"{u['username']}@example.com" == parsed_result[i]["email"]
        assert u["groups"] == ast.literal_eval(parsed_result[i]["groups"])


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        users_count=Mock(side_effect=lambda: len(TEST_KEYCLOAK_USERS)),
        get_users=Mock(
            side_effect=lambda: [
                {
                    "id": u["id"],
                    "username": u["username"],
                    "email": f"{u['username']}@example.com",
                }
                for u in TEST_KEYCLOAK_USERS
            ]
        ),
        get_user_groups=Mock(
            side_effect=lambda user_id: [
                {"name": g}
                for u in TEST_KEYCLOAK_USERS
                if u["id"] == user_id
                for g in u["groups"]
            ]
        ),
    ),
)
def test_cli_keycloak_listusers_happy_path_from_config(_mock_keycloak_admin):
    result = run_cli_keycloak_listusers(use_env=False)

    assert 0 == result.exit_code
    assert not result.exception

    parsed_result = parse_table(result.stdout, ["username", "email", "groups"])

    # output should start with the number of users found then
    # display a table with their info
    assert len(TEST_KEYCLOAK_USERS) == len(parsed_result)

    for i, u in enumerate(TEST_KEYCLOAK_USERS):
        assert u["username"] == parsed_result[i]["username"]
        assert f"{u['username']}@example.com" == parsed_result[i]["email"]
        assert u["groups"] == ast.literal_eval(parsed_result[i]["groups"])


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        get_groups=Mock(
            side_effect=lambda: TEST_KEYCLOAK_GROUPS,
        ),
        get_group_by_path=Mock(
            side_effect=lambda path: {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": path.strip("/"),
                "path": path,
                "attributes": {},
                "realmRoles": [],
                "clientRoles": TEST_KEYCLOAK_GROUP_CLIENT_ROLES[path],
                "subGroups": [],
            }
        ),
    ),
)
def test_cli_keycloak_listgroups_happy_path_from_env(_mock_keycloak_admin):
    result = run_cli_keycloak_listgroups(use_env=True)
    assert 0 == result.exit_code
    assert not result.exception

    parsed_result = parse_yaml(result.stdout, ["name", "roles"])

    parsed_result_dict = {item["name"]: item["roles"] for item in parsed_result}

    for group_path, expected_roles in TEST_KEYCLOAK_GROUP_CLIENT_ROLES.items():
        group_name = group_path.strip("/")
        assert group_name in parsed_result_dict
        assert (
            get_expected_roles(expected_roles, group_name)
            == parsed_result_dict[group_name]
        )


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        get_groups=Mock(
            side_effect=lambda: TEST_KEYCLOAK_GROUPS,
        ),
        get_group_by_path=Mock(
            side_effect=lambda path: {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": path.strip("/"),
                "path": path,
                "attributes": {},
                "realmRoles": [],
                "clientRoles": TEST_KEYCLOAK_GROUP_CLIENT_ROLES[path],
                "subGroups": [],
            }
        ),
    ),
)
def test_cli_keycloak_listgroups_happy_path_from_config(_mock_keycloak_admin):
    result = run_cli_keycloak_listgroups(use_env=False)
    assert 0 == result.exit_code
    assert not result.exception

    parsed_result = parse_yaml(result.stdout, ["name", "roles"])

    parsed_result_dict = {item["name"]: item["roles"] for item in parsed_result}

    for group_path, expected_roles in TEST_KEYCLOAK_GROUP_CLIENT_ROLES.items():
        group_name = group_path.strip("/")
        assert group_name in parsed_result_dict
        assert (
            get_expected_roles(expected_roles, group_name)
            == parsed_result_dict[group_name]
        )


@patch(
    "keycloak.KeycloakAdmin.__init__",
    side_effect=keycloak.exceptions.KeycloakConnectionError(
        error_message="connection test"
    ),
)
def test_cli_keycloak_listusers_keycloak_connection_exception(_mock_keycloak_admin):
    result = run_cli_keycloak_listusers()

    assert 1 == result.exit_code
    assert result.exception
    assert "Failed to connect to Keycloak server: connection test" in str(
        result.exception
    )


@patch(
    "keycloak.KeycloakAdmin.__init__",
    side_effect=keycloak.exceptions.KeycloakAuthenticationError(
        error_message="auth test"
    ),
)
def test_cli_keycloak_listusers_keycloak_auth_exception(_mock_keycloak_admin):
    result = run_cli_keycloak_listusers()

    assert 1 == result.exit_code
    assert result.exception
    assert "Failed to connect to Keycloak server: auth test" in str(result.exception)


@patch(
    "keycloak.KeycloakAdmin",
    return_value=Mock(
        users_count=Mock(
            side_effect=keycloak.exceptions.KeycloakConnectionError(
                error_message="unhandled"
            )
        ),
    ),
)
def test_cli_keycloak_listusers_keycloak_unhandled_error(_mock_keycloak_admin):
    result = run_cli_keycloak_listusers()

    assert 1 == result.exit_code
    assert result.exception
    assert "unhandled" == str(result.exception)


def mock_api_post(admin_password: str, url: str, headers: Any, data: Any, verify: bool):
    response = Mock()
    if (
        url
        == f"{MOCK_KEYCLOAK_ENV['KEYCLOAK_SERVER_URL']}realms/master/protocol/openid-connect/token"
        and data["password"] == admin_password
    ):
        response.status_code = 200
        response.content = bytes(
            json.dumps({"access_token": TEST_ACCESS_TOKEN}), "UTF-8"
        )
    else:
        response.status_code = 403
    return response


def mock_api_request(
    access_token: str, method: str, url: str, headers: Any, verify: bool
):
    response = Mock()
    if (
        method == "GET"
        and url
        == f"{MOCK_KEYCLOAK_ENV['KEYCLOAK_SERVER_URL']}admin/realms/test-realm/users"
        and headers["Authorization"] == f"Bearer {access_token}"
    ):
        response.status_code = 200
        response.content = bytes(json.dumps(TEST_KEYCLOAK_USERS), "UTF-8")
    else:
        response.status_code = 403
    return response


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        TEST_ACCESS_TOKEN, method, url, headers, verify
    ),
)
def test_cli_keycloak_exportusers_happy_path_from_env(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_keycloak_exportusers()

    assert 0 == result.exit_code
    assert not result.exception

    r = json.loads(result.stdout)
    assert "test-realm" == r["realm"]
    assert 3 == len(r["users"])
    assert "test-dev" == r["users"][0]["username"]


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        TEST_ACCESS_TOKEN, method, url, headers, verify
    ),
)
def test_cli_keycloak_exportusers_happy_path_from_config(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_keycloak_exportusers(use_env=False)

    assert 0 == result.exit_code
    assert not result.exception

    r = json.loads(result.stdout)
    assert "test-realm" == r["realm"]
    assert 3 == len(r["users"])
    assert "test-dev" == r["users"][0]["username"]


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        "invalid_admin_password", url, headers, data, verify
    ),
)
def test_cli_keycloak_exportusers_error_authentication(_mock_requests_post):
    result = run_cli_keycloak_exportusers()

    assert 1 == result.exit_code
    assert result.exception
    assert "Unable to retrieve Keycloak API token" in str(result.exception)
    assert "Status code: 403" in str(result.exception)


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        "invalid_access_token", method, url, headers, verify
    ),
)
def test_cli_keycloak_exportusers_error_authorization(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_keycloak_exportusers()

    assert 1 == result.exit_code
    assert result.exception
    assert "Unable to communicate with Keycloak API" in str(result.exception)
    assert "Status code: 403" in str(result.exception)


@patch(
    "_nebari.keycloak.requests.post", side_effect=requests.exceptions.RequestException()
)
def test_cli_keycloak_exportusers_request_exception(_mock_requests_post):
    result = run_cli_keycloak_exportusers()

    assert 1 == result.exit_code
    assert result.exception


@patch("_nebari.keycloak.requests.post", side_effect=Exception())
def test_cli_keycloak_exportusers_unhandled_error(_mock_requests_post):
    result = run_cli_keycloak_exportusers()

    assert 1 == result.exit_code
    assert result.exception


def run_cli_keycloak(command: str, use_env: bool, extra_args: List[str] = []):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        extra_config = (
            {
                "domain": TEST_DOMAIN,
                "security": {
                    "keycloak": {
                        "initial_root_password": MOCK_KEYCLOAK_ENV[
                            "KEYCLOAK_ADMIN_PASSWORD"
                        ]
                    }
                },
            }
            if not use_env
            else {}
        )
        config = {**{"project_name": "keycloak"}, **extra_config}
        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(config, f)

        assert tmp_file.exists() is True

        app = create_cli()

        args = [
            "keycloak",
            command,
            "--config",
            tmp_file.resolve(),
        ] + extra_args

        env = MOCK_KEYCLOAK_ENV if use_env else {}
        result = runner.invoke(app, args=args, env=env)

        return result


def run_cli_keycloak_adduser(use_env: bool = True):
    username = TEST_KEYCLOAK_USERS[0]["username"]
    password = "test-password-123!"

    return run_cli_keycloak(
        "add-user",
        use_env=use_env,
        extra_args=[
            "--user",
            username,
            "--password",
            password,
        ],
    )


def run_cli_keycloak_listusers(use_env: bool = True):
    return run_cli_keycloak(
        "list-users",
        use_env=use_env,
    )


def run_cli_keycloak_listgroups(use_env: bool = True):
    return run_cli_keycloak(
        "list-groups",
        use_env=use_env,
    )


def run_cli_keycloak_exportusers(use_env: bool = True):
    return run_cli_keycloak(
        "export-users",
        use_env=use_env,
        extra_args=[
            "--realm",
            "test-realm",
        ],
    )
