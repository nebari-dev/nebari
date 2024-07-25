import logging
import re
import time
from pathlib import Path
from typing import List, Union

from tests.common.navigator import Navigator

logger = logging.getLogger()


class Notebook:
    def __init__(self, navigator: Navigator):
        self.nav = navigator
        self.nav.initialize

    def run(
        self,
        path,
        expected_outputs: List[str],
        conda_env: str,
        timeout: float = 1000,
        complition_wait_time: float = 2,
        retry: int = 2,
        retry_wait_time: float = 5,
        exact_match: bool = True,
    ):
        """Run jupyter notebook and check for expected output text anywhere on
        the page.

        Note: This will look for and exact match of expected_output_text
        _anywhere_ on the page so be sure that your text is unique.

        Conda environments may still be being built shortly after deployment.

        Parameters
        ----------
        path: str
            Path to notebook relative to the root of the jupyterlab instance.
        expected_outputs: List[str]
            Text to look for in the output of the notebook. This can be a
            substring of the actual output if exact_match is False.
        conda_env: str
            Name of conda environment. Python conda environments have the
            structure "conda-env-nebari-git-nebari-git-dashboard-py" where
            the actual name of the environment is "dashboard".
        timeout: float
            Time in seconds to wait for the expected output text to appear.
            default: 1000
        complition_wait_time: float
            Time in seconds to wait between checking for expected output text.
            default: 2
        retry: int
            Number of times to retry running the notebook.
            default: 2
        retry_wait_time: float
            Time in seconds to wait between retries.
            default: 5
        exact_match: bool
            If True, the expected output must match exactly. If False, the
            expected output must be a substring of the actual output.
            default: True
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

        for _ in range(retry):
            self._restart_run_all()
            # Wait for a couple of seconds to make sure it's re-started
            time.sleep(retry_wait_time)
            self._wait_for_commands_completion(timeout, complition_wait_time)
            all_outputs = self._get_outputs()
            assert_match_all_outputs(expected_outputs, all_outputs, exact_match)

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

    def assert_code_output(
        self,
        code: str,
        expected_output: str,
        timeout: float = 1000,
        complition_wait_time: float = 2,
        exact_match: bool = True,
    ):
        """
        Run code in last cell and check for expected output text anywhere on
        the page.


        Parameters
        ----------
        code: str
            Code to run in last cell.
        expected_outputs: List[Union[re.Pattern, str]]
            Text to look for in the output of the notebook.
        timeout: float
            Time in seconds to wait for the expected output text to appear.
            default: 1000
        complition_wait_time: float
            Time in seconds to wait between checking for expected output text.
        """
        self.run_in_last_cell(code)
        self._wait_for_commands_completion(timeout, complition_wait_time)
        outputs = self._get_outputs()
        actual_output = outputs[-1] if outputs else ""
        assert_match_output(expected_output, actual_output, exact_match)

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

    def _wait_for_commands_completion(
        self, timeout: float, complition_wait_time: float
    ):
        """
        Wait for commands to finish running

        Parameters
        ----------
        timeout: float
            Time in seconds to wait for the expected output text to appear.
        complition_wait_time: float
        Time in seconds to wait between checking for expected output text.
        """
        elapsed_time = 0.0
        still_visible = True
        start_time = time.time()
        while elapsed_time < timeout:
            running = self.nav.page.get_by_text("[*]").all()
            still_visible = any(list(map(lambda r: r.is_visible(), running)))
            if not still_visible:
                break
            elapsed_time = time.time() - start_time
            time.sleep(complition_wait_time)
        if still_visible:
            raise ValueError(
                f"Timeout Waited for commands to finish, "
                f"but couldn't finish in {timeout} sec"
            )

    def _get_outputs(self) -> List[str]:
        output_elements = self.nav.page.query_selector_all(".jp-OutputArea-output")
        text_content = [element.text_content().strip() for element in output_elements]
        return text_content

    def _restart_run_all(self):
        # restart run all cells
        self.nav.page.get_by_role("menuitem", name="Kernel", exact=True).click()
        self.nav.page.get_by_role(
            "menuitem", name="Restart Kernel and Run All Cells…"
        ).get_by_text("Restart Kernel and Run All Cells…").click()

        # Restart dialog appears most, but not all of the time (e.g. set
        # No Kernel, then Restart Run All)
        restart_dialog_button = self.nav.page.get_by_role(
            "button", name="Confirm Kernel Restart"
        )
        if restart_dialog_button.is_visible():
            restart_dialog_button.click()


def assert_match_output(
    expected_output: str, actual_output: str, exact_match: bool
) -> None:
    """Assert that the expected_output is found in the actual_output.

    ----------
    Parameters

    expected_output: str
        The expected output text or regular expression to find in the
        actual output.
    actual_output: str
        The actual output text to search for the expected output.
    exact_match: bool
        If True, then the expected_output must match the actual_output
        exactly. Otherwise, the expected_output must be found somewhere in
        the actual_output.
    """
    regex = re.compile(rf"{expected_output}")
    match = (
        regex.fullmatch(actual_output) if exact_match else regex.search(actual_output)
    )
    assert (
        match is not None
    ), f"Expected output: {expected_output} not found in actual output: {actual_output}"


def assert_match_all_outputs(
    expected_outputs: List[str],
    actual_outputs: List[str],
    exact_matches: Union[bool, List[bool]],
) -> None:
    """Assert that the expected_outputs are found in the actual_outputs.
    The expected_outputs and actual_outputs must be the same length.

    ----------
    Parameters

    expected_outputs: List[str]
        A list of expected output text or regular expression to find in
        the actual output.
    actual_outputs: List[str]
        A list of actual output text to search for the expected output.
    exact_matches: Union[bool, List[bool]]
        If True, then the expected_output must match the actual_output
        exactly. Otherwise, the expected_output must be found somewhere in
        the actual_output. If a list is provided, then it must be the same
        length as expected_outputs and actual_outputs.
    """
    if isinstance(exact_matches, bool):
        exact_matches = [exact_matches] * len(expected_outputs)

    for exact_output, actual_output, exact in zip(
        expected_outputs, actual_outputs, exact_matches
    ):
        assert_match_output(exact_output, actual_output, exact)
