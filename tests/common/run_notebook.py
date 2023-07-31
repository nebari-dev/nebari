import logging
import re
import time
from pathlib import Path

from tests.common.navigator import Navigator

logger = logging.getLogger()


class Notebook:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def run(
        self,
        path,
        expected_outputs,
        conda_env,
        runtime=30000,
        retry=2,
        exact_match=True,
    ):
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
        self.open_notebook(path)
        # make sure the focus is on the dashboard tab we want to run
        self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()
        self.nav.set_environment(kernel=conda_env)

        # make sure that this notebook is one currently selected
        self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()

        for i in range(retry):
            self._restart_run_all()
            # Wait for a couple of seconds to make sure it's re-started
            time.sleep(2)
            self._wait_for_commands_completion()
            all_outputs = self._get_outputs()
            self.assert_match_all_outputs(expected_outputs, all_outputs)

    def create_notebook(self, conda_env=None):
        file_locator = self.nav.page.get_by_text("File", exact=True)
        file_locator.wait_for(
            timeout=self.nav.wait_for_server_spinup,
            state="attached",
        )
        file_locator.click()
        submenu = self.nav.page.locator('[data-type="submenu"]').all()
        submenu[0].click()
        self.nav.page.get_by_role("menuitem", name="Notebook").get_by_text(
            "Notebook", exact=True
        ).click()
        self.nav.page.wait_for_load_state("networkidle")
        # make sure the focus is on the dashboard tab we want to run
        # self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()
        self.nav.set_environment(kernel=conda_env)

    def open_notebook(self, path):
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
            "Could not find path:",
            exact=False,
        ).is_visible():
            logger.debug("Path to notebook is invalid")
            raise RuntimeError("Path to notebook is invalid")

    def assert_code_output(self, code, expected_output):
        self.run_in_last_cell(code)
        self._wait_for_commands_completion()
        outputs = self._get_outputs()
        self.assert_match_output(expected_output, outputs[-1])

    def run_in_last_cell(self, code):
        self._create_new_cell()
        cell = self._get_last_cell()
        cell.click()
        cell.type(code)
        # Wait for it to be ready to be executed
        time.sleep(1)
        cell.press("Shift+Enter")
        # Wait for execution to start
        time.sleep(0.5)

    def _create_new_cell(self):
        new_cell_button = self.nav.page.query_selector(
            'button[data-command="notebook:insert-cell-below"]'
        )
        new_cell_button.click()

    def _get_last_cell(self):
        cells = self.nav.page.locator(".CodeMirror-code").all()
        for cell in reversed(cells):
            if cell.is_visible():
                return cell
        raise ValueError("Unable to get last cell")

    def _wait_for_commands_completion(self, timeout=120):
        elapsed_time = 0
        start_time = time.time()
        still_visible = True
        while elapsed_time < timeout:
            running = self.nav.page.get_by_text("[*]").all()
            still_visible = any(list(map(lambda r: r.is_visible(), running)))
            elapsed_time = time.time() - start_time
            time.sleep(1)
            if not still_visible:
                break
        if still_visible:
            raise ValueError(
                f"Timeout Waited for commands to finish, "
                f"but couldn't finish in {timeout} sec"
            )

    def _get_outputs(self):
        output_elements = self.nav.page.query_selector_all(".jp-OutputArea-output")
        text_content = [element.text_content().strip() for element in output_elements]
        return text_content

    def assert_match_all_outputs(self, expected_outputs, actual_outputs):
        for ex, act in zip(expected_outputs, actual_outputs):
            self.assert_match_output(ex, act)

    def assert_match_output(self, expected_output, actual_output):
        if isinstance(expected_output, re.Pattern):
            assert re.match(expected_output, actual_output)
        else:
            assert expected_output == actual_output

    def _restart_run_all(self):
        # restart run all cells
        self.nav.page.get_by_text("Kernel", exact=True).click()
        self.nav.page.get_by_role(
            "menuitem", name="Restart Kernel and Run All Cells…"
        ).get_by_text("Restart Kernel and Run All Cells…").click()

        # Restart dialog appears most, but not all of the time (e.g. set
        # No Kernel, then Restart Run All)
        restart_dialog_button = self.nav.page.get_by_role(
            "button", name="Restart", exact=True
        )
        if restart_dialog_button.is_visible():
            restart_dialog_button.click()
