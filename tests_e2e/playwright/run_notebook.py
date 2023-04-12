import logging
import os
from pathlib import Path

import dotenv
from navigator import Navigator

logger = logging.getLogger()


class RunNotebook:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def run_notebook(self, path, expected_output_text, conda_env, runtime=30000):
        """Run jupyter notebook and check for expected output text anywhere on
        the page.

        Note: This will look for and exact match of expected_output_text
        _anywhere_ on the page so be sure that your text is unique.

        Conda environments may still be being built shortly after deployment.

        conda_env: str
            Name of conda environment. Python conda environments have the
            structure "conda-env-nebari-git-nebari-git-dashboard-py" where
            the actual name of the environment is "dashboard".
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
        self.nav.set_environment(kernel=conda_env)

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
        instance_name="small-instance",
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
        conda_env="conda-env-default-py",
    )
    nav.teardown()
