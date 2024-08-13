import pytest
from playwright.sync_api import expect

from tests.common.handlers import CondaStore, Notebook
from tests.common.playwright_fixtures import login_parameterized, server_parameterized


@login_parameterized()
def test_login_logout(navigator):
    expect(navigator.page.get_by_text(navigator.username)).to_be_visible()

    navigator.logout()
    expect(navigator.page.get_by_text("Sign in with Keycloak")).to_be_visible()


@pytest.mark.parametrize(
    "services",
    [
        (
            [
                "Home",
                "Token",
                "User Management",
                "Argo Workflows",
                "Environment Management",
                "Monitoring",
            ]
        ),
    ],
)
@login_parameterized()
def test_navbar_services(navigator, services):
    navigator.page.goto(navigator.nebari_url + "hub/home")
    navigator.page.wait_for_load_state("networkidle")
    navbar_items = navigator.page.locator("#thenavbar").get_by_role("link")
    navbar_items_names = [item.text_content() for item in navbar_items.all()]
    assert len(navbar_items_names) == len(services)
    assert navbar_items_names == services


@pytest.mark.parametrize(
    "expected_outputs",
    [
        (["success: 6"]),
    ],
)
@server_parameterized(instance_name="small-instance")
def test_notebook(navigator, test_data_root, expected_outputs):
    notebook_manager = Notebook(navigator=navigator)

    notebook_manager.reset_workspace()

    notebook_name = "test_notebook_output.ipynb"
    notebook_path = test_data_root / notebook_name

    assert notebook_path.exists()

    with open(notebook_path, "r") as notebook:
        notebook_manager.write_file(filepath=notebook_name, content=notebook.read())

    outputs = notebook_manager.run_notebook(
        notebook_name=notebook_name, kernel="default"
    )

    assert outputs == expected_outputs

    # Clean up
    notebook_manager.reset_workspace()


@pytest.mark.parametrize(
    "namespaces",
    [
        (["analyst", "developer", "global", "nebari-git", "users"]),
    ],
)
@server_parameterized(instance_name="small-instance")
def test_conda_store_ui(navigator, namespaces):
    conda_store = CondaStore(navigator=navigator)

    conda_store.reset_workspace()

    conda_store.conda_store_ui()

    shown_namespaces = conda_store._get_shown_namespaces()
    shown_namespaces.sort()

    namespaces.append(navigator.username)
    namespaces.sort()

    assert shown_namespaces == namespaces
    # Clean up
    conda_store.reset_workspace()
