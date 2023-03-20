import os

import dotenv
from basic import Navigator, RunNotebook


def test_notebook(browser_name):
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev",
        google_email=os.environ["GOOGLE_EMAIL"],
        username=os.environ["GOOGLE_EMAIL"],
        google_password=os.environ["GOOGLE_PASSWORD"],
        headless=True,
        browserr=browser_name,
    )
    nav.google_login_start_server()
    nav.reset_workspace()
    test_app = RunNotebook(navigator=nav)
    test_app.run_notebook(
        path="test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
    nav.teardown()
