from basic import RunNotebook


def test_notebook(navigator):
    test_app = RunNotebook(navigator=navigator)
    test_app.run_notebook(
        path="test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
