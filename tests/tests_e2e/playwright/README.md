# Nebari integration testing with Playwright


## How does it work?

Playwright manages interactions with any website. We are using it to interact
with a deployed Nebari instance and test the various integrations that are
included.

For our test suite, we utilize Playwright's synchronous API. The first task
is to launch the web browser you'd like to test in. Options in our test suite
are `chromium`, `webkit`, and `firefox`. Playwright uses browser contexts to
achieve test isolation. The context can either be created by default or
manually (for the purposes of generating multiple contexts per test in the case
of admin vs user testing). Next the page on the browser is created. For all
tests this starts as a blank page, then during the test, we navigate to a given
url. This is all achieved in the `setup` method of the `Navigator` class.

## Setup

Install Nebari with the development requirements (which include Playwright)

`pip install -e ".[dev]"`

Then install playwright itself (required).

`playwright install`

> If you see the warning `BEWARE: your OS is not officially supported by Playwright; downloading fallback build., it is not critical.` Playwright will likely still work microsoft/playwright#15124

### Create environment file

Create a copy of the `.env` template file

```bash
cd tests_e2e/playwright
cp .env.tpl .env
```

Fill in the newly created `.env` file with the following values:

* KEYCLOAK_USERNAME: Nebari username for username/password login OR Google email address or Google sign in
* KEYCLOAK_PASSWORD: Password associated with USERNAME
* NEBARI_FULL_URL: full url path including scheme to Nebari instance, e.g. "https://nebari.quansight.dev/"

This user can be created with the following command (or you can use an existing non-root user):

```
nebari keycloak adduser --user <username> <password> --config <NEBARI_CONFIG_PATH>
```

## Running the Playwright tests

The playwright tests are run inside of pytest using

```python
pytest tests_e2e/playwright/test_playwright.py
```

Videos of the test playback will be available in `$PWD/videos/`.
To see what is happening while the test is run, pass the `--headed` option to `pytest`.
You can also add the `--slowmo=$MILLI_SECONDS` option to add a delay before each action
by Playwright and thus slowing down the process.

Another option is to run playwright methods outside of pytest. Both
`navigator.py` and `run_notebook.py` can be run as scripts. For example,

```python
    import os

    import dotenv
    # load environment variables from .env file
    dotenv.load_dotenv()
    # instantiate the navigator class
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev/",
        username=os.environ["KEYCLOAK_USERNAME"],
        password=os.environ["KEYCLOAK_PASSWORD"],
        auth="password",
        instance_name="small-instance",
        headless=False,
        slow_mo=100,
    )
    # go through login sequence (defined by `auth` method in Navigator class)
    nav.login()
    # start the nebari server (defined by `instance_type` in Navigator class)
    nav.start_server()
    # reset the jupyterlab workspace to ensure we're starting with only the
    # Launcher screen open, and we're in the root directory.
    nav.reset_workspace()
    # instantiate our test application
    test_app = RunNotebook(navigator=nav)
    # Write the sample notebook on the nebari instance
    notebook_filepath_in_repo = (
        "tests_e2e/playwright/test_data/test_notebook_output.ipynb"
    )
    notebook_filepath_on_nebari = "test_notebook_output.ipynb"
    with open(notebook_filepath_in_repo, "r") as notebook:
        test_app.nav.write_file(
            filepath=notebook_filepath_on_nebari, content=notebook.read()
        )
    # run a sample notebook
    test_app.run_notebook(
        path="nebari/tests_e2e/playwright/test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
        conda_env="conda-env-default-py",
    )
    # close out playwright and its associated browser handles
    nav.teardown()
```

## Writing Playwright tests

In general most of the testing happens through `locators` which is Playwright's
way of connecting a python object to the HTML element on the page.
The Playwright API has several mechanisms for getting a locator for an item on
the page (`get_by_role`, `get_by_text`, `get_by_label`, `get_by_placeholder`,
etc).

```python
button = self.page.get_by_role("button", name="Sign in with Keycloak")
```

Once you have a handle on a locator, you can interact with it in different ways,
depending on the type of object. For example, clicking
a button:

```python
button.click()
```

Occasionally you'll need to wait for things to load on the screen. We can
either wait for the page to finish loading:

```python
self.page.wait_for_load_state("networkidle")
```

or we can wait for something specific to happen with the locator itself:

```python
button.wait_for(timeout=3000, state="attached")
```

Note that waiting for the page to finish loading may be deceptive inside of
Jupyterlab since things may need to load _inside_ the page, not necessarily
causing network traffic - or causing several bursts network traffic, which
would incorrectly pass the `wait_for_load_state` after the first burst.

Playwright has a built-in auto-wait feature which waits for a timeout period
for some actionable items. See https://playwright.dev/docs/actionability .

### Workflow for creating new tests

An example of running a new run notebook test might look like this:

```python
    import os

    import dotenv
    # load environment variables from .env file
    dotenv.load_dotenv()
    # instantiate the navigator class
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev/",
        username=os.environ["KEYCLOAK_USERNAME"],
        password=os.environ["KEYCLOAK_PASSWORD"],
        auth="password",
        instance_name="small-instance",
        headless=False,
        slow_mo=100,
    )
    # go through login sequence (defined by `auth` method in Navigator class)
    nav.login()
    # start the nebari server (defined by `instance_type` in Navigator class)
    nav.start_server()
    # reset the jupyterlab workspace to ensure we're starting with only the
    # Launcher screen open, and we're in the root directory.
    nav.reset_workspace()
    # instantiate our test application
    test_app = RunNotebook(navigator=nav)
    # Write the sample notebook on the nebari instance
    notebook_filepath_in_repo = (
        "tests_e2e/playwright/test_data/test_notebook_output.ipynb"
    )
    notebook_filepath_on_nebari = "test_notebook_output.ipynb"
    with open(notebook_filepath_in_repo, "r") as notebook:
        test_app.nav.write_file(
            filepath=notebook_filepath_on_nebari, content=notebook.read()
        )
    # run a sample notebook
    test_app.run_notebook(
        path="nebari/tests_e2e/playwright/test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
        conda_env="conda-env-default-py",
    )
    # close out playwright and its associated browser handles
    nav.teardown()
```
