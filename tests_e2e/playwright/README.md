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

Then install playwright itself (rerquired).

`playwright install`

> If you see the warning `BEWARE: your OS is not officially supported by Playwright; downloading fallback build., it is not critical.` Playwright will likely still work microsoft/playwright#15124

### Create environment file

Create a copy of the `.env` template file

```bash
cp .env.tpl .env
```

Fill in the newly created `.env` file with the following values:

* USERNAME: Nebari username for username/password login OR Google email address or Google sign in
* PASSWORD: Password associated with USERNAME
* NEBARI_FULL_URL: full url path to Nebari instance, e.g. "https://nebari.quansight.dev/"

## Running the Playwright tests

The playwright tests are run inside of pytest using

```python
pytest tests_e2e/playwright/test_playwright.py
```

Videos of the test playback will be available in `tests_e2e/playwright/videos/`.

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
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
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
    # clone the nebari repo into the nebari instance
    test_app.nav.clone_repo(
        "https://github.com/nebari-dev/nebari.git",
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

**If you are creating a new notebook to be run** (or a test that requires a new
file), the you will have to push your changes up to a branch, then be sure to
clone that branch into Nebari in order to use the new files.

An example of running a new run notebook test might look like this:

```python
    import os

    import dotenv
    # load environment variables from .env file
    dotenv.load_dotenv()
    # instantiate the navigator class
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev/",
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
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
    # clone the nebari repo into the nebari instance
    test_app.nav.clone_repo(
        "https://github.com/nebari-dev/nebari.git", branch="add_playwright"
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

Where you're new notebook only exists on the `add_playwright` branch of
`https://github.com/nebari-dev/nebari.git`.

Another alternative to pushing changes to your file up to the repo for every
test is to work off on existing nebari deployment.


**If you are making changes to the Nebari codebase** and not changes to the
tests, then you can just run the playwright tests inside of `test_playwright.py`
without pushing up new files or modifying the repo clone.
