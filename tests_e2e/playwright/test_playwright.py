import os

from basic import Navigator, RunNotebook


def test_login():
    nav = Navigator(
        nebari_url=os.environ["NEBARI_FULL_URL"],
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        headless=False,
        browser="chromium",
        auth="password",
        instance_name=os.environ["INSTANCE_NAME"],
        video_dir="videos/",
    )
    nav.login_password()
    nav.start_server()
    nav.teardown()


def test_notebook(navigator):
    test_app = RunNotebook(navigator=navigator)
    test_app.run_notebook(
        path="test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
