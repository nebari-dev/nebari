from run_notebook import RunNotebook


def test_notebook(navigator, test_data_root):
    test_app = RunNotebook(navigator=navigator)
    notebook_name = "test_notebook_output.ipynb"
    with open(test_data_root / notebook_name, "r") as notebook:
        test_app.nav.write_file(filepath=notebook_name, content=notebook.read())
    test_app.run_notebook(
        path=notebook_name,
        expected_output_text="success: 6",
        conda_env="conda-env-default-py",
        runtime=60000,
    )
