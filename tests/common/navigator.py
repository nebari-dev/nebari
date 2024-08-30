import logging
import re
import urllib
from abc import ABC
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

logger = logging.getLogger()


class NavigatorMixin(ABC):
    """
    A mixin class providing common setup and teardown functionalities for Playwright navigators.
    """

    def __init__(
        self,
        headless=False,
        slow_mo=0,
        browser="chromium",
        video_dir=None,
        video_name_prefix=None,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser_name = browser
        self.video_dir = video_dir
        self.video_name_prefix = video_name_prefix
        self.initialized = False
        self.setup()

    def setup(self):
        """Setup Playwright browser and context."""
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

    def _rename_test_video_path(self, video_path):
        """Rename the test video file to the test unique identifier."""
        video_file_name = (
            f"{self.video_name_prefix}.mp4" if self.video_name_prefix else None
        )
        if video_file_name and video_path:
            Path.rename(video_path, Path(self.video_dir) / video_file_name)

    def teardown(self) -> None:
        """Teardown Playwright browser and context."""
        if self.initialized:
            # Rename the video file to the test unique identifier
            current_video_path = self.page.video.path()
            self._rename_test_video_path(current_video_path)

            self.context.close()
            self.browser.close()
            self.playwright.stop()
            logger.debug(">>> Teardown complete.")
            self.initialized = False

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.teardown()


class LoginNavigator(NavigatorMixin):
    """
    A navigator class to handle login operations for Nebari.
    """

    def __init__(self, nebari_url, username, password, auth="password", **kwargs):
        super().__init__(**kwargs)
        self.nebari_url = nebari_url
        self.username = username
        self.password = password
        self.auth = auth

    def login(self):
        """Login to Nebari deployment using the provided authentication method."""
        login_methods = {
            "google": self._login_google,
            "password": self._login_password,
        }
        try:
            login_methods[self.auth]()
        except KeyError:
            raise ValueError(f"Auth type {self.auth} is invalid.")

    def logout(self):
        """Logout from Nebari deployment."""
        self.page.get_by_role("button", name="Logout").click()
        self.page.wait_for_load_state

    def _login_google(self):
        logger.debug(">>> Sign in via Google and start the server")
        self.page.goto(self.nebari_url)
        expect(self.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.page.get_by_role("button", name="Sign in with Keycloak").click()
        self.page.get_by_role("link", name="Google").click()
        self.page.get_by_role("textbox", name="Email or phone").fill(self.username)
        self.page.get_by_role("button", name="Next").click()
        self.page.get_by_role("textbox", name="Enter your password").fill(self.password)
        self.page.get_by_role("button", name="Next").click()
        self.page.wait_for_load_state("networkidle")

    def _login_password(self):
        logger.debug(">>> Sign in via Username/Password")
        self.page.goto(self.nebari_url)
        expect(self.page).to_have_url(re.compile(f"{self.nebari_url}*"))

        self.page.get_by_role("button", name="Sign in with Keycloak").click()
        self.page.get_by_label("Username").fill(self.username)
        self.page.get_by_label("Password").fill(self.password)
        self.page.get_by_role("button", name="Sign In").click()
        self.page.wait_for_load_state()

        # Redirect to hub control panel
        self.page.goto(urllib.parse.urljoin(self.nebari_url, "hub/home"))
        expect(self.page.get_by_role("button", name="Logout")).to_be_visible()


class ServerManager(LoginNavigator):
    """
    Manages server operations such as starting and stopping a Nebari server.
    """

    def __init__(
        self, instance_name="small-instance", wait_for_server_spinup=300_000, **kwargs
    ):
        super().__init__(**kwargs)
        self.instance_name = instance_name
        self.wait_for_server_spinup = wait_for_server_spinup

    def start_server(self):
        """Start a Nebari server, handling different UI states."""
        self.login()

        logout_button = self.page.get_by_text("Logout", exact=True)
        logout_button.wait_for(state="attached", timeout=90000)

        start_locator = self.page.get_by_role("button", name="My Server", exact=True)
        if start_locator.is_visible():
            start_locator.click()
        else:
            start_locator = self.page.get_by_role("button", name="Start My Server")
            if start_locator.is_visible():
                start_locator.click()

        server_options = self.page.get_by_role("heading", name="Server Options")
        if server_options.is_visible():
            self.page.locator(f"#profile-item-{self.instance_name}").click()
            self.page.get_by_role("button", name="Start").click()

        self.page.wait_for_url(re.compile(f".*user/{self.username}/.*"), timeout=180000)
        file_locator = self.page.get_by_text("File", exact=True)
        file_locator.wait_for(state="attached", timeout=self.wait_for_server_spinup)

        logger.debug(">>> Profile Spawn complete.")

    def stop_server(self):
        """Stops the Nebari server via the Hub Control Panel."""
        self.page.get_by_text("File", exact=True).click()
        with self.context.expect_page() as page_info:
            self.page.get_by_role("menuitem", name="Home", exact=True).click()

        home_page = page_info.value
        home_page.wait_for_load_state()
        stop_button = home_page.get_by_role("button", name="Stop My Server")
        stop_button.wait_for(state="visible")
        stop_button.click()
        stop_button.wait_for(state="hidden")


# Factory method for creating different navigators if needed
def navigator_factory(navigator_type, **kwargs):
    navigators = {
        "login": LoginNavigator,
        "server": ServerManager,
    }
    return navigators[navigator_type](**kwargs)
