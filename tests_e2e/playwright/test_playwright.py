import os

import dotenv
from basic import Navigator, RunNotebook


def test_notebook(browser_name):
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url=os.environ["NEBARI_BASE_URL"],
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        headless=True,
        browser=browser_name,
        auth="password",
        instance_name="small-instance",
    )
    nav.login_password()
    nav.start_server()
    nav.reset_workspace()
    test_app = RunNotebook(navigator=nav)
    test_app.run_notebook(
        path="test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
    nav.teardown()
