import contextlib
import datetime as dt
import logging
import re
import time
import urllib

from playwright.sync_api import expect, sync_playwright

logger = logging.getLogger()


class Navigator:
    """Base class for Nebari Playwright testing. This provides setup and
    teardown methods that all tests will need and some other generally useful
    methods such as clearing the workspace. Specific tests such has "Run a
    notebook" are included in separate classes which use an instance of
    this class.

    The Navigator class and the associated test classes are design to be able
    to run either standalone, or inside of pytest. This makes it easy to
    develop new tests, but also have them fully prepared to be
    included as part of the test suite.

    Parameters
    ----------
    nebari_url: str
        Nebari URL to access for testing, e.g. "https://{nebari_url}
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
        self.wait_for_server_spinup = 300_000  # 5 * 60 * 1_000  # 5 minutes in ms

    @property
    def initialize(self):
        """Ensure that the Navigator is setup and ready for testing."""
        if not self.initialized:
            self.setup(
                browser=self.browser,
                headless=self.headless,
                slow_mo=self.slow_mo,
            )

    def setup(self, browser, headless, slow_mo):
        """Initial setup for running playwright. Starts playwright, creates
        the browser object, a new browser context, and a new page object.

        Parameters
        ----------
        browser: str
            Browser on which to run tests. Options are "chromium",
            "webkit", and "firefox".
        headless: bool
            Run the tests in headless mode (without visuals) if True
        slow_mo: int
            Additional milliseconds to add to each Playwright command,
            creating the effect of running the tests in slow motion so they are
            easier for humans to follow.
        """
        logger.debug(">>> Setting up browser for Playwright")

        self.playwright = sync_playwright().start()
        try:
            self.browser = getattr(self.playwright, browser).launch(
                headless=headless, slow_mo=slow_mo
            )
        except AttributeError:
            raise RuntimeError(f"{browser} browser is not recognized.") from None
        self.context = self.browser.new_context(
            ignore_https_errors=True,
            record_video_dir=self.video_dir,
        )
        self.page = self.context.new_page()
        self.initialized = True

    def teardown(self) -> None:
        """Shut down and close playwright. This is important to ensure that
        no leftover processes are left running in the background."""
        self.context.close()
        self.browser.close()  # Make sure to close, so that videos are saved.
        self.playwright.stop()
        logger.debug(">>> Teardown complete.")

    def login(self) -> None:
        """Login to nebari deployment using the auth method on the class."""
        try:
            return {
                "google": self.login_google,
                "password": self.login_password,
            }[self.auth]()
        except KeyError:
            raise ValueError(f"Auth type of {self.auth} is invalid.") from None

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
        """Start a nebari server. There are several different web interfaces
        possible in this process depending on if you already have a server
        running or not. In order for this to work, wait for the page to load,
        we look for html elements that exist when no server is running, if
        they aren't visible, we check for an existing server start option.
        """
        # wait for the page to load
        logout_button = self.page.get_by_text("Logout", exact=True)
        logout_button.wait_for(state="attached")

        # if server is not yet running
        start_locator = self.page.get_by_role("button", name="Start My Server")
        if start_locator.is_visible():
            start_locator.click()

            # select instance type (this will fail if this instance type is not
            # available)
            self.page.locator(f"#profile-item-{self.instance_name}").click()
            self.page.get_by_role("button", name="Start").click()

        else:
            # if the server is already running
            start_locator = self.page.get_by_role(
                "button",
                name="My Server",
                exact=True,
            )
            start_locator.click()

        # wait for server spinup
        self.page.wait_for_url(
            urllib.parse.urljoin(self.nebari_url, f"user/{self.username}/*"),
            wait_until="networkidle",
        )

        # the jupyter page loads independent of network activity so here
        # we wait for the File menu to be available on the page, a proxy for
        # the jupyterlab page being loaded.
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
        """Reset the Jupyterlab workspace.

        * Closes all Tabs & handle possible popups for saving changes,
        * make sure any kernel popups are dealt with
        * reset file browser is reset to root
        * Finally, ensure that the Launcher screen is showing
        """
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
        with contextlib.suppress(Exception):
            shut_down_all = self.page.get_by_text(
                "Shut Down All Kernels...", exact=True
            )
            shut_down_all.wait_for(timeout=300, state="attached")
            shut_down_all.click()

        # shut down kernel if only one notebook is running
        kernel_menuitem.click()
        with contextlib.suppress(Exception):
            shut_down_current = self.page.get_by_text("Shut Down Kernel", exact=True)
            shut_down_current.wait_for(timeout=300, state="attached")
            shut_down_current.click()

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

        # wait to ensure that the Launcher is showing
        self.page.get_by_text("VS Code [↗]", exact=True).wait_for(
            timeout=3000, state="attached"
        )

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
            # failure here indicates that the environment doesn't exist either
            # because of incorrect naming syntax or because the env is still
            # being built
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

        Conda environments may still be being built shortly after deployment.

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

        # wait for the jupyter UI to catch up before moving forward
        # extract conda env name
        conda_env_label = re.search("conda-env-(.*)-py", kernel).group(1)
        # see if the jupyter notebook label for the conda env is visible
        kernel_label_loc = self.page.get_by_role("button", name=conda_env_label)
        if not kernel_label_loc.is_visible():
            kernel_label_loc.wait_for(state="attached")

    def clone_repo(self, git_url, branch=None, wait_for_completion=5):
        """Clone a git repo into the jupyterlab file structure.

        The terminal is a blackbox for the browser. We can't access any of the
        displayed text, therefore we have no way of knowing if the commands
        are done executing. For this reason, there is an unavoidable sleep
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
        start = dt.datetime.now()

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

        # TODO temporary to check if environments are built
        self.page.get_by_role("textbox", name="Terminal input").fill("conda env list")
        self.page.get_by_role("textbox", name="Terminal input").press("Enter")

        logger.debug(f"time to complete {dt.datetime.now() - start}")
        # ensure that playwright doesn't move on/change context until all the
        # above commands are complete.
        time.sleep(wait_for_completion)
        self.reset_workspace()


if __name__ == "__main__":
    import os

    import dotenv

    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev/",
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        auth="password",
        instance_name="small-instance",
        headless=False,
        slow_mo=100,
    )
    nav.login()
    nav.start_server()
    nav.reset_workspace()
    nav.teardown()
