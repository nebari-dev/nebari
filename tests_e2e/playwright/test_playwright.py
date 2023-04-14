from run_notebook import RunNotebook


def test_notebook(navigator):
    test_app = RunNotebook(navigator=navigator)
    test_app.nav.clone_repo(
        "https://github.com/nebari-dev/nebari.git",
        branch="add_playwright",
        wait_for_completion=30,
    )
    test_app.run_notebook(
        path="nebari/tests_e2e/playwright/test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
        conda_env="conda-env-default-py",
        runtime=60000,
    )
