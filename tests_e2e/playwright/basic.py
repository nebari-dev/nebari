import logging
import os
import re

import dotenv
from playwright.sync_api import expect, sync_playwright

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(level=logging.DEBUG)
formatter = logging.Formatter("%(levelname)s : %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)


class Navigator:
    """Base class for Nebari Playwright testing. This provides setup and
    teardown methods that all tests will need and some other generally useful
    methods such as clearing the workspace. Specific tests such has "Run a
    notebook" will be a separate class which inherits from this one. It will
    leverage the base class and add other specific tests.

    Navigator classes are able to run either standalone, or inside of pytest.
    This makes it easy to develop new tests, but also fully prepared to be
    included as part of the test suite.
    """

    def __init__(
        self,
        nebari_url,
        google_email,
        username,
        google_password,
        headless=False,
        slow_mo=100,
        playwright=None,
        browser=None,
        context=None,
        page=None,
    ):
        self.nebari_url = nebari_url
        self.google_email = google_email
        self.google_password = google_password
        self.username = username
        self.initialized = False

        self.setup()
        self.wait_for_server_spinup = 5 * 60 * 1000  # 5 minutes in ms

    @property
    def initialize(self):
        if not self.initialized:
            self.setup()

    def setup(self, browser="chromium", headless=False, slow_mo=100):
        logger.debug(">>> Setting up browser for Playwright")

        self.playwright = sync_playwright().start()
        if browser == "chromium":
            self.browser = self.playwright.chromium.launch(
                headless=headless, slow_mo=slow_mo
            )
        elif browser == "webkit":
            self.browser = self.playwright.webkit.launch(
                headless=headless, slow_mo=slow_mo
            )
        elif browser == "firefox":
            self.browser = self.playwright.firefox.launch(
                headless=headless, slow_mo=slow_mo
            )
        else:
            raise RuntimeError(f"{browser} browser is not recognized.")
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.initialized = True

    def teardown(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
        logger.debug(">>> Teardown complete.")

    def google_login_start_server(self) -> None:
        """Go to a nebari deployment, login via Google, and start a new server."""
        logger.debug(">>> Sign in via Google and start the server")
        self.page.goto(self.nebari_url)
        expect(self.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.page.get_by_role("button", name="Sign in with Keycloak").click()
        self.page.get_by_role("link", name="Google").click()
        self.page.get_by_role("textbox", name="Email or phone").fill(self.google_email)
        self.page.get_by_role("button", name="Next").click()
        self.page.get_by_role("textbox", name="Enter your password").fill(
            self.google_password
        )

        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("button", name="Next").click()

        self.page.wait_for_load_state(
            "networkidle"
        )  # let the page load (use this to avoid a long wait in the try statement)

        # if server is not yet running
        start_locator = self.page.get_by_role("button", name="Start My Server")
        try:
            start_locator.wait_for(timeout=3000, state="attached")
            start_locator.click()

            # your server is not yet running, would like to start it?
            self.page.get_by_role("button", name="Launch server").click()
            # select instance type
            self.page.locator(
                "#profile-item-small-instance-with-conda-store-ui"
            ).click()
            self.page.get_by_role("button", name="Start").click()

        except Exception:
            # if the server is already running
            start_locator = self.page.get_by_role(
                "button", name="My Server", exact=True
            )
            start_locator.wait_for(timeout=3000, state="attached")

            start_locator.click()

        # wait for redirect
        self.page.wait_for_url(f"{self.nebari_url}/user/{self.username}/*")
        # let page load after redirect
        self.page.wait_for_load_state("networkidle")

    def _check_for_kernel_popup(self):
        """Is the kernel popup currently open?

        Returns
        -------
        True if the kernel popup is open.
        """
        self.page.wait_for_load_state("networkidle")
        visible = self.page.get_by_text("Select Kernel", exact=True).is_visible()

        return visible

    def reset_workspace(self):
        logger.debug(">>> Reset JupyterLab workspace")

        # server is already running and there is no popup
        popup = self._check_for_kernel_popup()

        # server is on running and there is a popup
        if popup:
            self._set_environment_via_popup(kernel=None)

        # go to Kernel menu
        kernel_menuitem = self.page.get_by_text("Kernel", exact=True)
        kernel_menuitem.click()
        # shut down multiple running kernels
        try:
            shut_down_all = self.page.get_by_text(
                "Shut Down All Kernels...", exact=True
            )
            shut_down_all.wait_for(timeout=300, state="attached")
            shut_down_all.click()
        except Exception:
            logger.debug('Did not find "Shut Down All" menu option')

        # shut down kernel if only one notebook is running
        kernel_menuitem.click()
        try:
            shut_down_current = self.page.get_by_text("Shut Down Kernel", exact=True)
            shut_down_current.wait_for(timeout=300, state="attached")
            shut_down_current.click()
        except Exception:
            logger.debug('Did not find "Shut Down Kernel" menu option')

        # go back to root folder
        self.page.get_by_title(f"/home/{self.google_email}", exact=True).locator(
            "path"
        ).click()

        # go to File menu
        self.page.get_by_text("File", exact=True).click()
        # close all tabs
        self.page.get_by_role("menuitem", name="Close All Tabs", exact=True).click()

        # there may be a popup to save your work, don't save
        if self.page.get_by_text("Save your work", exact=True).is_visible():
            self.page.get_by_role("button", name="Discard", exact=True).click()

    def _set_environment_via_popup(self, kernel=None):
        """Set the environment kernel via the popup dialog box.
        If kernel is `None`, `No Kernel` is selected and the popup is dismissed.

        Attributes
        ----------
        kernel: str or None
            (Optional) name of conda environment to set. Defaults to None.

        """
        if kernel is None:
            # close dialog (deal with the two formats of this dialog)
            try:
                self.page.get_by_text("Cancel", exact=True).click()
            except Exception:
                self.page.locator("div").filter(has_text="No KernelSelect").get_by_role(
                    "button", name="No Kernel"
                ).wait_for(timeout=300, state="attached")
        else:
            # set the environment
            self.page.get_by_role("combobox").nth(1).select_option(
                f'{{"name":"{kernel}"}}'
            )
            # click Select to close popup (deal with the two formats of this dialog)
            try:
                self.page.get_by_role("button", name="Select", exact=True).click()
            except Exception:
                self.page.locator("div").filter(has_text="No KernelSelect").get_by_role(
                    "button", name="Select"
                ).click()

    def set_environment(self, kernel):
        """The focus MUST be on the dashboard we are trying to run"""

        popup = self._check_for_kernel_popup()
        # if there is not a kernel popup, make it appear
        if not popup:
            self.page.get_by_text("Kernel", exact=True).click()
            self.page.get_by_role("menuitem", name="Change Kernel…").get_by_text(
                "Change Kernel…"
            ).click()

        self._set_environment_via_popup(kernel)


class RunNotebook:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def run_notebook(self, path, expected_output_text):
        logger.debug(">>> Run test notebook")

        # TODO: add nbgitpuller here?

        # navigate to specific notebook
        file_locator = self.nav.page.get_by_text("File", exact=True)

        file_locator.wait_for(
            timeout=300000, state="attached"
        )  # 5 minutes max for server to spin up
        file_locator.click()
        self.nav.page.get_by_role("menuitem", name="Open from Path…").get_by_text(
            "Open from Path…"
        ).click()
        self.nav.page.get_by_placeholder("/path/relative/to/jlab/root").fill(path)
        self.nav.page.get_by_role("button", name="Open").click()
        # give the page a second to open, otherwise the options in the kernel menu will be disabled.
        self.nav.page.wait_for_load_state("networkidle")
        # make sure the focus is on the dashboard tab we want to run
        self.nav.page.get_by_role("tab", name=path).get_by_text(path).click()
        self.nav.set_environment(kernel="conda-env-global-global-dashboard-v3-py")

        # make sure that this notebook is one currently selected
        self.nav.page.get_by_role("tab", name=path).get_by_text(path).click()

        # restart run all cells
        self.nav.page.get_by_text("Kernel", exact=True).click()
        self.nav.page.get_by_role(
            "menuitem", name="Restart Kernel and Run All Cells…"
        ).get_by_text("Restart Kernel and Run All Cells…").click()
        self.nav.page.get_by_role("button", name="Restart", exact=True).click()

        # expect(self.nav.page.get_by_text(expected_output_text, exact=True)).to_have_text(f"{expected_output_text}") # not sure why this doesn't work
        assert self.nav.page.get_by_text(expected_output_text, exact=True).is_visible()


if __name__ == "__main__":
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev",
        google_email=os.environ["GOOGLE_EMAIL"],
        username=os.environ["GOOGLE_EMAIL"],
        google_password=os.environ["GOOGLE_PASSWORD"],
    )
    nav.google_login_start_server()
    nav.reset_workspace()
    test_app = RunNotebook(navigator=nav)
    test_app.run_notebook(
        path="test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
    nav.teardown()
