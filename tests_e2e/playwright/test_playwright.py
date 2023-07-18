from run_notebook import RunNotebook


def test_notebook(navigator):
    test_app = RunNotebook(navigator=navigator)
    notebook_filepath_in_repo = (
        "test_data/test_notebook_output.ipynb"
    )
    notebook_filepath_on_nebari = "test_notebook_output.ipynb"
    with open(notebook_filepath_in_repo, "r") as notebook:
        test_app.nav.write_file(
            filepath=notebook_filepath_on_nebari, content=notebook.read()
        )
    test_app.run_notebook(
        path=notebook_filepath_on_nebari,
        expected_output_text="success: 6",
        conda_env="conda-env-default-py",
        runtime=60000,
    )
