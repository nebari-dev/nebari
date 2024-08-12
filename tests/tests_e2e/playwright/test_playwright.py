import time

from tests.common.playwright_fixtures import server_parameterized, login_parameterized

from tests.common.run_notebook import Notebook


# @navigator_parameterized(instance_name="small-instance")
# def test_notebook(navigator, test_data_root):
#     test_app = Notebook(navigator=navigator)
#     notebook_name = "test_notebook_output.ipynb"
#     notebook_path = test_data_root / notebook_name
#     assert notebook_path.exists()
#     with open(notebook_path, "r") as notebook:
#         test_app.nav.write_file(filepath=notebook_name, content=notebook.read())
#     test_app.run(
#         path=notebook_name,
#         expected_outputs=["success: 6"],
#         conda_env="default",
#         timeout=500,
#     )


@login_parameterized()
def test_main_hub(navigator):
    navigator.page.goto(navigator.nebari_url)
    # expect(navigator.page.locator("Nebari")).to_be_visible(


@server_parameterized(instance_name="small-instance")
def test_notebook(navigator, test_data_root):
    time.sleep(15)
