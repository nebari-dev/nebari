import logging
import os
import re
from pathlib import Path
import time

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

    Parameters
    ----------
    nebari_url: str
        Nebari URL to access for testing
    username: str
        Login username for Nebari. For Google login, this will be email address.
    password: str
        Login password for Nebari. For Google login, this will be the Google
        password.
    auth: str
        Authentication type of this Nebari instance. Options are "google" and
        "password".
    headless: bool
        (Optional) Run the tests in headless mode (without visuals). Defaults
        to False.
    slow_mo: int
        (Optional) Additional milliseconds to add to each Playwright command,
        creating the effect of running the tests in slow motion so they are
        easier for humans to follow. Defaults to 0.
    browser: str
        (Optional) Browser on which to run tests. Options are "chromium",
        "webkit", and "firefox". Defaults to "chromium".
    instance_name: str
        (Optional) Server instance type on which to run tests. Options are
        based on the configuration of the Nebari instance. Defaults to
        "small-instance". Note that special characters (such as parenthesis)
        will need to be converted to dashes. Check the HTML element to get the
        exact structure.
    video_dir: None or str
        (Optional) Directory in which to save videos. If None, no video will
        be saved. Defaults to None.
    """

    def __init__(
        self,
        nebari_url,
        username,
        password,
        auth,
        headless=False,
        slow_mo=0,
        browser="chromium",
        instance_name="small-instance",
        video_dir=None,
    ):
        self.nebari_url = nebari_url
        self.username = username
        self.password = password
        self.auth = auth
        self.initialized = False
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = browser
        self.instance_name = instance_name
        self.video_dir = video_dir

        self.setup(
            browser=self.browser,
            headless=self.headless,
            slow_mo=self.slow_mo,
        )
        self.wait_for_server_spinup = 30000  # 5 * 60 * 1000  # 5 minutes in ms

    @property
    def initialize(self):
        if not self.initialized:
            self.setup(
                browser=self.browser,
                headless=self.headless,
                slow_mo=self.slow_mo,
            )

    def setup(self, browser, headless, slow_mo):
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
        self.context = self.browser.new_context(
            ignore_https_errors=True,
            record_video_dir=self.video_dir,
        )
        self.page = self.context.new_page()
        self.initialized = True

    def teardown(self):
        self.context.close()
        self.browser.close()  # Make sure to close, so that videos are saved.
        self.playwright.stop()
        logger.debug(">>> Teardown complete.")

    def login(self) -> None:
        if self.auth == "google":
            self.login_google()
        elif self.auth == "password":
            self.login_password()
        else:
            raise ValueError(f"Auth type of {self.auth} is invalid.")

    def login_google(self) -> None:
        """Go to a nebari deployment, login via Google"""
        logger.debug(">>> Sign in via Google and start the server")
        self.page.goto(self.nebari_url)
        expect(self.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.page.get_by_role("button", name="Sign in with Keycloak").click()
        self.page.get_by_role("link", name="Google").click()
        self.page.get_by_role("textbox", name="Email or phone").fill(self.username)
        self.page.get_by_role("button", name="Next").click()
        self.page.get_by_role("textbox", name="Enter your password").fill(self.password)

        self.page.wait_for_load_state("networkidle")
        self.page.get_by_role("button", name="Next").click()

        # let the page load
        self.page.wait_for_load_state("networkidle")

    def login_password(self) -> None:
        """Go to a nebari deployment, login via Username/Password, and start
        a new server.
        """
        logger.debug(">>> Sign in via Username/Password")
        self.page.goto(self.nebari_url)
        expect(self.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.page.get_by_role("button", name="Sign in with Keycloak").click()
        self.page.get_by_label("Username").fill(self.username)
        self.page.get_by_label("Password").click()
        self.page.get_by_label("Password").fill(self.password)
        self.page.get_by_role("button", name="Sign In").click()

        # let the page load
        self.page.wait_for_load_state("networkidle")

    def start_server(self) -> None:
        # if server is not yet running
        start_locator = self.page.get_by_role("button", name="Start My Server")
        try:
            start_locator.wait_for(timeout=3000, state="attached")
            start_locator.click()

            # I'm not sure why this is no longer needed. Leaving it here for
            # future reference.
            # # your server is not yet running, would like to start it?
            # self.page.get_by_role("button", name="Launch server").click()

            # select instance type (TODO will fail if this instance type is not
            # available)
            self.page.locator(f"#profile-item-{self.instance_name}").click()
            self.page.get_by_role("button", name="Start").click()

            # # wait for server to spinup
            # server_message = self.page.get_by_text(
            #     f"Server ready at /user/{self.username}/",
            #     exact=True,
            # )
            # server_message.wait_for(
            #     timeout=self.wait_for_server_spinup,
            #     state="attached",
            # )

        except Exception:
            # if the server is already running
            start_locator = self.page.get_by_role(
                "button",
                name="My Server",
                exact=True,
            )
            start_locator.wait_for(timeout=3000, state="attached")
            start_locator.click()

        # server spinup https://nebari.quansight.dev/hub/spawn-pending/kcpevey@quansight.com
        # wait for redirect - be wary of extra slashes here! https://nebari.quansight.dev/user/kcpevey@quansight.com/lab
        # the jupyter page loads independent of the url???
        self.page.wait_for_url(
            f"{self.nebari_url}user/{self.username}/*", wait_until="networkidle"
        )  # why did this not work on the latest ci test???? # TODO on friday!!

        # # let page load after redirect
        # self.page.wait_for_load_state("networkidle")

        file_locator = self.page.get_by_text("File", exact=True)
        file_locator.wait_for(
            timeout=self.wait_for_server_spinup,
            state="attached",
        )

        logger.debug(">>> Sign in complete.")

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
            pass

        # shut down kernel if only one notebook is running
        kernel_menuitem.click()
        try:
            shut_down_current = self.page.get_by_text("Shut Down Kernel", exact=True)
            shut_down_current.wait_for(timeout=300, state="attached")
            shut_down_current.click()
        except Exception:
            pass

        # go back to root folder
        self.page.get_by_title(f"/home/{self.username}", exact=True).locator(
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
        """Set the environment kernel on a jupyter notebook via the popup
        dialog box. If kernel is `None`, `No Kernel` is selected and the
        popup is dismissed.

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
        """Set environment of a jupyter notebook.

        IMPORTANT: The focus MUST be on the notebook on which you want to set
        the environment.

        Parameters
        ----------
        kernel: str
            Name of kernel to set.

        Returns
        -------
        None
        """

        popup = self._check_for_kernel_popup()
        # if there is not a kernel popup, make it appear
        if not popup:
            self.page.get_by_text("Kernel", exact=True).click()
            self.page.get_by_role("menuitem", name="Change Kernel…").get_by_text(
                "Change Kernel…"
            ).click()

        self._set_environment_via_popup(kernel)

    def clone_repo(self, git_url, branch=None):
        """Clone a git repo into the jupyterlab file structure.

        The terminal is a blackbox for the browser. We can't access any of the
        displayed text, therefore we have no way of knowing if the commands
        are done excecuting. For this reason, there is an unavoidable sleep
        here that prevents playwright from moving on to ensure that the focus
        remains on the Terminal until we are done issuing our commands. 

        Parameters
        ----------
        git_url: str
            url of git repo (must be public, referenced as http rather than ssh
            format, e.g. https://github.com/nebari-dev/nebari.git)
        branch: bool or str
            (Optional) branch to checkout from the repo. Defaults to None to use
            the default branch.

        Returns
        -------
        None
        """
        logger.debug(f">>> Clone git repo: {git_url}")

        input_string = f"git clone {git_url}"
        if branch:
            input_string = f"{input_string} --branch {branch}"
        self.page.get_by_text("File", exact=True).click()
        self.page.get_by_text("New", exact=True).click()
        self.page.get_by_role("menuitem", name="Terminal").get_by_text(
            "Terminal"
        ).click()
        self.page.get_by_role("textbox", name="Terminal input").fill(input_string)
        self.page.get_by_role("textbox", name="Terminal input").press("Enter")

        # TODO temporarily checkout this branch so that it has the notebook to test
        self.page.get_by_role("textbox", name="Terminal input").fill("cd nebari")
        self.page.get_by_role("textbox", name="Terminal input").press("Enter")
        self.page.get_by_role("textbox", name="Terminal input").fill("git checkout add_playwright")
        self.page.get_by_role("textbox", name="Terminal input").press("Enter")
        
        # ensure that playwright doesn't move on/change context until all the 
        # above commands are complete.
        time.sleep(20) 
        self.reset_workspace()


class RunNotebook:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def run_notebook(self, path, expected_output_text, runtime=30000):
        """Run jupyter notebook and check for expected output text anywhere on
        the page.

        Note: This will look for and exact match of expected_output_text
        _anywhere_ on the page so be sure that your text is unique.
        """
        logger.debug(f">>> Running notebook: {path}")
        filename = Path(path).name

        # navigate to specific notebook
        file_locator = self.nav.page.get_by_text("File", exact=True)

        file_locator.wait_for(
            timeout=self.nav.wait_for_server_spinup,
            state="attached",
        )
        file_locator.click()
        self.nav.page.get_by_role("menuitem", name="Open from Path…").get_by_text(
            "Open from Path…"
        ).click()
        self.nav.page.get_by_placeholder("/path/relative/to/jlab/root").fill(path)
        self.nav.page.get_by_role("button", name="Open", exact=True).click()
        # give the page a second to open, otherwise the options in the kernel
        # menu will be disabled.
        self.nav.page.wait_for_load_state("networkidle")
        if self.nav.page.get_by_text(
            f"Could not find path: {path}", exact=True
        ).is_visible():
            logger.debug("Path to notebook is invalid")
            raise RuntimeError("Path to notebook is invalid")
        # make sure the focus is on the dashboard tab we want to run
        self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()
        self.nav.set_environment(kernel="conda-env-nebari-git-nebari-git-dashboard-py")

        # make sure that this notebook is one currently selected
        self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()

        # restart run all cells
        self.nav.page.get_by_text("Kernel", exact=True).click()
        self.nav.page.get_by_role(
            "menuitem", name="Restart Kernel and Run All Cells…"
        ).get_by_text("Restart Kernel and Run All Cells…").click()
        self.nav.page.get_by_role("button", name="Restart", exact=True).click()

        # expect(self.nav.page.get_by_text(
        #     expected_output_text, exact=True
        #     )).to_have_text(f"{expected_output_text}"
        #     ) # not sure why this doesn't work
        output_locator = self.nav.page.get_by_text(expected_output_text, exact=True)
        output_locator.wait_for(timeout=runtime)  # wait for notebook to run
        assert output_locator.is_visible()


if __name__ == "__main__":
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev/",
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        auth="password",
        instance_name="small-instance-w-jupyterlab-conda-store-v0-2-7",
        headless=False,
        slow_mo=100,
    )
    nav.login()
    nav.start_server()
    nav.reset_workspace()
    test_app = RunNotebook(navigator=nav)
    test_app.nav.clone_repo(
        "https://github.com/nebari-dev/nebari.git", branch="add_playwright"
    )
    test_app.run_notebook(
        path="nebari/tests_e2e/playwright/test_data/test_notebook_output.ipynb",
        expected_output_text="success: 6",
    )
    nav.teardown()
