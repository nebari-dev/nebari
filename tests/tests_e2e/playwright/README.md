
# Nebari Integration Testing with Playwright

## How Does It Work?

Playwright manages interactions with websites, and we use it to interact with a deployed Nebari instance and test various integrations.

We use Playwright's synchronous API for our test suite. The first task is to launch the web browser of your choice: `chromium`, `webkit`, or `firefox`. Playwright uses browser contexts for test isolation, which can be created by default or manually for scenarios like admin vs. user testing. Each test starts with a blank page, and we navigate to a given URL during the test. This setup is managed by the `setup` method in the `Navigator` class.

## Directory Structure

The project directory structure is as follows:

```
tests
├── common
│   ├── __init__.py
│   ├── navigator.py
│   ├── handlers.py
│   ├── playwright_fixtures.py
├── ...
├── tests_e2e
│   └── playwright
│       ├── README.md
│       └── test_playwright.py
```

- `test_data/`: Contains test files, such as sample notebooks.
- `test_playwright.py`: The main test script that uses Playwright for integration testing.
- `navigator.py`: Contains the `NavigatorMixin` class, which manages browser
  interactions and context. As well as the `LoginNavigator` class, which manages user
  authentication and `ServerManager` class, which manages the user instance spawning.
- `handlers.py`: Contains classes fore handling the different level of access to
  services a User might encounter, such as Notebook, Conda-store and others.

## Setup

1. **Install Nebari with Development Requirements**

   Install Nebari including development requirements (which include Playwright):

   ```bash
   pip install -e ".[dev]"
   ```

2. **Install Playwright**

   Install Playwright:

   ```bash
   playwright install
   ```

   *Note:* If you see the warning `BEWARE: your OS is not officially supported by Playwright; downloading fallback build`, it is not critical. Playwright should still work (see microsoft/playwright#15124).

3. **Create Environment Vars**

   Fill in your execution space environment with the following values:

   - `KEYCLOAK_USERNAME`: Nebari username for username/password login or Google email address/Google sign-in.
   - `KEYCLOAK_PASSWORD`: Password associated with `KEYCLOAK_USERNAME`.
   - `NEBARI_FULL_URL`: Full URL path including scheme to the Nebari instance (e.g., "https://nebari.quansight.dev/").

   This user can be created with the following command (or use an existing non-root user):

   ```bash
   nebari keycloak adduser --user <username> <password> --config <NEBARI_CONFIG_PATH>
   ```

## Running the Playwright Tests

Playwright tests are run inside of pytest using:

```bash
pytest tests_e2e/playwright/test_playwright.py
```

Videos of the test playback will be available in `$PWD/videos/`. To disabled the browser
runtime preview of what is happening while the test runs, pass the `--headed` option to `pytest`. You
can also add the `--slowmo=$MILLI_SECONDS` option to introduce a delay before each
action by Playwright, thereby slowing down the process.

Alternatively, you can run Playwright methods outside of pytest. Below an example of
how to run a test, where you can interface with the Notebook handler:

```python
import os
import dotenv
from pathlib import Path

from tests.common.navigator import ServerManager
from tests.common.handlers import Notebook


# Instantiate the Navigator class
nav = ServerManage(
    nebari_url="https://nebari.quansight.dev/",
    username=os.environ["KEYCLOAK_USERNAME"],
    password=os.environ["KEYCLOAK_PASSWORD"],
    auth="password",
    instance_name="small-instance",
    headless=False,
    slow_mo=100,
)


notebook_manager = Notebook(navigator=navigator)

# Reset the JupyterLab workspace to ensure we're starting with only the Launcher screen open and in the root directory.
notebook_manager.reset_workspace()

notebook_name = "test_notebook_output.ipynb"
notebook_path = Path("tests_e2e/playwright/test_data") / notebook_name

assert notebook_path.exists()

# Write the sample notebook on the Nebari instance
with open(notebook_path, "r") as notebook:
    notebook_manager.write_file(filepath=notebook_name, content=notebook.read())

# Run a sample notebook (and collect the outputs)
outputs = notebook_manager.run_notebook(
    notebook_name=notebook_name, kernel="default"
)

# Close out Playwright and its associated browser handles
nav.teardown()
```

## Writing Playwright Tests

Most testing is done through `locators`, which connect Python objects to HTML elements on the page. Playwright offers several mechanisms for getting a locator for an item on the page, such as `get_by_role`, `get_by_text`, `get_by_label`, and `get_by_placeholder`.

```python
button = self.page.get_by_role("button", name="Sign in with Keycloak")
```

Once you have a handle on a locator, you can interact with it in various ways, depending on the type of object. For example, clicking a button:

```python
button.click()
```

Sometimes you'll need to wait for elements to load on the screen. You can wait for the page to finish loading:

```python
self.page.wait_for_load_state("networkidle")
```

Or wait for something specific to happen with the locator itself:

```python
button.wait_for(timeout=3000, state="attached")
```

Note that waiting for the page to finish loading may be misleading inside of JupyterLab since elements may need to load _inside_ the page or cause several bursts of network traffic.

Playwright has a built-in auto-wait feature that waits for a timeout period for actionable items. See [Playwright Actionability](https://playwright.dev/docs/actionability).

## Parameterized Decorators

### Usage

Parameterized decorators in your test setup allow you to run tests with different configurations or contexts. They are particularly useful for testing different scenarios, such as varying user roles or application states.

To easy the control over the initial setup of spawning the user instance and login, we
already provider two base decorators that can be used in your test:
- `server_parameterized`: Allows to login and spin a new instance of the server, based
  on the provided instance type. Allows for the nav.page to be run within the JupyterLab environment.
- ` login_parameterized`: Allow login to Nebari and sets you test workspace to the main
  hub, allow your tests to attest things like the launcher screen or the navbar components.

For example, using parameterized decorators to test different user roles might look like this:

```python
@pytest.mark.parametrize("is_admin", [False])
@login_parameterized()
def test_role_button(navigator, is_admin):
    _ = navigator.page.get_by_role("button", name="Admin Button").is_visible()
    assert _ == is_admin
    # Perform tests specific to the user role...
```
In the example above, we used the `login_parameterized` decorator which will log in as an user
(based on the KEYCLOAK_USERNAME and KEYCLOAK_PASSWORD) and and let you wander under the logged workspace,
we attest for the presence of the "Admin Button" in the page (which does not exist).

If your test suit presents a need for a more complex sequence of actions or special
parsing around the contents present in each page, you can create
your own handler to execute the auxiliary actions while the test is running. Check the
`handlers.py` over some examples of how that's being done.
