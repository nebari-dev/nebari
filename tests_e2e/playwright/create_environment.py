import logging
import os

import dotenv
from basic import Navigator

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(level=logging.DEBUG)
formatter = logging.Formatter("%(levelname)s : %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)


class CreateEnvironment:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def create_environment(
        self,
    ):
        """Create simple environment."""
        logger.debug(">>> Creating environment")
        self.nav.page.get_by_role("menuitem", name="Conda-Store").click()
        self.nav.page.get_by_text("Conda Store Package Manager").click()
        self.nav.page.get_by_role("tabpanel", name="conda-store").get_by_role(
            "link"
        ).click()
        self.nav.page.get_by_text("Conda-Store").click()
        self.nav.page.get_by_text("Conda Store Package Manager").click()
        self.nav.page.get_by_role(
            "button",
            name="Create a new environment in the pwadhwa@quansight.com namespace",
            exact=True,
        ).click()
        self.nav.page.get_by_placeholder("Environment name").click()
        self.nav.page.get_by_placeholder("Environment name").fill("playwright-test")
        self.nav.page.get_by_role("button", name="+ Add Package").click()
        self.nav.page.get_by_label("Enter package").fill("python")
        self.nav.page.get_by_label("Enter package").press("Enter")
        self.nav.page.get_by_role("button", name="+ Add Package").click()
        self.nav.page.get_by_label("Enter package").fill("pandas")
        self.nav.page.get_by_label("Enter package").press("Enter")
        self.nav.page.get_by_role("button", name="Channels", exact=True).click()
        self.nav.page.get_by_role("button", name="+ Add Channel").click()
        self.nav.page.get_by_label("Enter channel").fill("conda-forge")
        self.nav.page.get_by_label("Enter channel").press("Enter")
        self.nav.page.get_by_role("button", name="Create", exact=True).click()


class Navigator(Navigator):
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
        super().__init__(
            nebari_url,
            username,
            password,
            auth,
            headless=False,
            slow_mo=0,
            browser="chromium",
            instance_name="small-instance",
            video_dir=None,
        )

    def start_server(self):
        start_locator = self.page.get_by_role("button", name="Start My Server")
        if start_locator.is_visible():
            logger.debug(">>> Starting server")
            self.page.get_by_role("button", name="Start My Server", exact=True).click()
            self.page.get_by_role("button", name="Start", exact=True).click()
        else:
            logger.debug(">>> Server has already started.")
            self.page.get_by_role("button", name="My Server", exact=True).click()


if __name__ == "__main__":
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url="https://nebari.quansight.dev",
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        auth="google",
        instance_name="small-instance-w-jupyterlab-conda-store-v0-2-7",
        headless=False,
        slow_mo=100,
    )
    nav.login()
    nav.start_server()
    test_app = CreateEnvironment(navigator=nav)
    test_app.create_environment()

    nav.teardown()
