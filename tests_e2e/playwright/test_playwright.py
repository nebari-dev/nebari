import dotenv
from basic import RunNotebook, Navigator
import os


def test_notebook():
    # TODO: Pam add the main test here
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url = 'https://nebari.quansight.dev',
        google_email= os.environ['GOOGLE_EMAIL'],
        username = os.environ['GOOGLE_EMAIL'],
        google_password = os.environ['GOOGLE_PASSWORD'],
    )
    nav.google_login_start_server()
    nav.reset_workspace()
    test_app = RunNotebook(navigator=nav)
    test_app.run_notebook(path='dashboard_panel.ipynb', expected_output_text='success 3333')
    nav.teardown()
