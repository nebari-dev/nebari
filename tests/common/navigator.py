import logging
import re
import urllib
from abc import abstractmethod

from playwright.sync_api import expect, sync_playwright

logger = logging.getLogger()


class BaseNavigator:
    """
    Base class for Playwright setup and teardown. This provides the necessary
    setup for browser and page context that can be used in subclasses for
    specific testing or navigation functionalities.

    Parameters
    ----------
    headless: bool
        (Optional) Run the tests in headless mode (without visuals). Defaults to False.
    slow_mo: int
        (Optional) Additional milliseconds to add to each Playwright command, creating the effect of running the tests in slow motion. Defaults to 0.
    browser: str
        (Optional) Browser on which to run tests. Options are "chromium", "webkit", and "firefox". Defaults to "chromium".
    video_dir: None or str
        (Optional) Directory in which to save videos. If None, no video will be saved. Defaults to None.
    """

    def __init__(self, headless=False, slow_mo=0, browser="chromium", video_dir=None):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser_name = browser
        self.video_dir = video_dir
        self.initialized = False
        self.setup()

    def setup(self):
        """Initial setup for running Playwright. Starts Playwright, creates
        the browser object, a new browser context, and a new page object."""
        logger.debug(">>> Setting up browser for Playwright")
        self.playwright = sync_playwright().start()
        try:
            self.browser = getattr(self.playwright, self.browser_name).launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
        except AttributeError:
            raise RuntimeError(
                f"{self.browser_name} browser is not recognized."
            ) from None
        self.context = self.browser.new_context(
            ignore_https_errors=True,
            record_video_dir=self.video_dir,
        )
        self.page = self.context.new_page()
        self.initialized = True

    def teardown(self) -> None:
        """Shut down and close Playwright. This is important to ensure that
        no leftover processes are left running in the background."""
        self.context.close()
        self.browser.close()  # Make sure to close, so that videos are saved.
        self.playwright.stop()
        logger.debug(">>> Teardown complete.")


class LoginManager:
    """
    Context manager for handling Nebari login operations. Manages authentication
    processes and ensures proper login/logout sequences.

    Parameters
    ----------
    base_navigator: BaseNavigator
        An instance of BaseNavigator for browser interaction.
    nebari_url: str
        Nebari URL to access for testing, e.g. "https://{nebari_url}"
    username: str
        Login username for Nebari. For Google login, this will be an email address.
    password: str
        Login password for Nebari. For Google login, this will be the Google password.
    auth: str
        Authentication type of this Nebari instance. Options are "google" and "password".
    """

    def __init__(self, base_navigator, nebari_url, username, password, auth):
        self.base_navigator = base_navigator
        self.nebari_url = nebari_url
        self.username = username
        self.password = password
        self.auth = auth

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self

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
        self.base_navigator.page.goto(self.nebari_url)
        expect(self.base_navigator.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.base_navigator.page.get_by_role(
            "button", name="Sign in with Keycloak"
        ).click()
        self.base_navigator.page.get_by_role("link", name="Google").click()
        self.base_navigator.page.get_by_role("textbox", name="Email or phone").fill(
            self.username
        )
        self.base_navigator.page.get_by_role("button", name="Next").click()
        self.base_navigator.page.get_by_role(
            "textbox", name="Enter your password"
        ).fill(self.password)

        self.base_navigator.page.wait_for_load_state("networkidle")
        self.base_navigator.page.get_by_role("button", name="Next").click()

        # let the page load
        self.base_navigator.page.wait_for_load_state("networkidle")

    def login_password(self) -> None:
        """Go to a nebari deployment, login via Username/Password."""
        logger.debug(">>> Sign in via Username/Password")
        self.base_navigator.page.goto(self.nebari_url)
        expect(self.base_navigator.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.base_navigator.page.get_by_role(
            "button", name="Sign in with Keycloak"
        ).click()
        self.base_navigator.page.get_by_label("Username").fill(self.username)
        self.base_navigator.page.get_by_label("Password").click()
        self.base_navigator.page.get_by_label("Password").fill(self.password)
        self.base_navigator.page.get_by_role("button", name="Sign In").click()

        # let the page load
        self.base_navigator.page.wait_for_load_state()

        # go to hub control panel
        self.base_navigator.page.goto(urllib.parse.urljoin(self.nebari_url, "hub/home"))

        # Check if user is logged in by looking for the logout button
        expect(
            self.base_navigator.page.get_by_role("button", name="Logout")
        ).to_be_visible()


class ServerManager(BaseNavigator):
    """
    Server manager for Nebari Playwright testing. Handles all server management
    functionalities such as starting, stopping, and configuring servers.

    Parameters
    ----------
    nebari_url: str
        Nebari URL to access for server management.
    username: str
        Username to verify user-specific URLs and pages.
    instance_name: str
        (Optional) Server instance type on which to run tests. Defaults to "small-instance".
    """

    def __init__(
        self,
        nebari_url,
        username,
        password,
        auth="password",
        instance_name="small-instance",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.nebari_url = nebari_url
        self.username = username
        self.password = password
        self.instance_name = instance_name
        self.auth = auth
        self.wait_for_server_spinup = 300_000  # 5 * 60 * 1_000  # 5 minutes in ms

    def run(self):
        """Wrapper to use LoginManager and run server-related tasks."""
        with LoginManager(
            base_navigator=self,
            nebari_url=self.nebari_url,
            username=self.username,
            password=self.password,
            auth=self.auth,
        ):
            # Run server-related methods after login
            return self.start()

    @abstractmethod
    def start(self):
        # Do wherever you want here
        return self.start_server()

    def start_server(self) -> None:
        """Start a nebari server. There are several different web interfaces
        possible in this process depending on if you already have a server
        running or not. In order for this to work, wait for the page to load,
        we look for html elements that exist when no server is running, if
        they aren't visible, we check for an existing server start option.
        """
        # wait for the page to load
        logout_button = self.page.get_by_text("Logout", exact=True)
        logout_button.wait_for(state="attached", timeout=90000)

        # if the server is already running
        start_locator = self.page.get_by_role("button", name="My Server", exact=True)
        if start_locator.is_visible():
            start_locator.click()

        # if server is not yet running
        start_locator = self.page.get_by_role("button", name="Start My Server")
        if start_locator.is_visible():
            start_locator.click()

        server_options = self.page.get_by_role("heading", name="Server Options")
        if server_options.is_visible():
            # select instance type (this will fail if this instance type is not
            # available)
            self.page.locator(f"#profile-item-{self.instance_name}").click()
            self.page.get_by_role("button", name="Start").click()

        # Confirm redirection to user's /lab page
        self.page.wait_for_url(
            re.compile(
                f".*user/{self.username}/.*",
            ),
            timeout=180000,
        )
        # the jupyter page loads independent of network activity so here
        # we wait for the File menu to be available on the page, a proxy for
        # the jupyterlab page being loaded.
        file_locator = self.page.get_by_text("File", exact=True)
        file_locator.wait_for(
            timeout=self.wait_for_server_spinup,
            state="attached",
        )

        logger.debug(">>> Profile Spawn complete.")

    def stop_server(self) -> None:
        """Stops the JupyterHub server by navigating to the Hub Control Panel."""
        self.page.get_by_text("File", exact=True).click()

        with self.context.expect_page() as page_info:
            self.page.get_by_role("menuitem", name="Home", exact=True).click()

        home_page = page_info.value
        home_page.wait_for_load_state()
        stop_button = home_page.get_by_role("button", name="Stop My Server")
        if not stop_button.is_visible():
            stop_button.wait_for(state="visible")
        stop_button.click()
        stop_button.wait_for(state="hidden")
