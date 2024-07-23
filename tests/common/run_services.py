import logging

from tests.common.navigator import Navigator

logger = logging.getLogger()


class Services:
    def __init__(self, navigator: Navigator):
        self.nav = navigator

    def run(
        self,
        timeout: float = 1000,
    ):
        """
        Access all associated deployment services endpoints availability as a user.

        Parameters
        ----------
        timeout: float
            Time in seconds to wait for the expected output text to appear.
            Default: 1000
        """
        logger.debug(">>> Running access services test")

        try:
            # Visit Conda-Store
            self.nav.page.goto("/conda-store/login/")
            self.nav.page.locator(
                'body > nav > a:has-text("conda-store")'
            ).get_attribute("href")

            # Visit Grafana Monitoring - user must have an email address in Keycloak
            self.nav.page.goto("/monitoring/dashboards")
            self.nav.page.locator("div#pageContent h1").wait_for(timeout=timeout)
            assert (
                self.nav.page.locator("div#pageContent h1").text_content()
                == "Dashboards"
            )

            # Visit Keycloak User Profile
            self.nav.page.goto("/auth/realms/nebari/account/#/personal-info")
            assert (
                self.nav.page.locator("input#user-name").input_value()
                == "EXAMPLE_USER_NAME"
            )

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
