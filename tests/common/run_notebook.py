import contextlib
import datetime as dt
import logging
import time

from playwright.sync_api import expect

from tests.common.navigator import ServerManager

logger = logging.getLogger()


class Notebook(ServerManager):
    def start(self): ...

    def _check_for_kernel_popup(self):
        """Is the kernel popup currently open?

        Returns
        -------
        True if the kernel popup is open.
        """
        logger.info("Checking for kernel popup")

        self.page.wait_for_load_state()
        time.sleep(3)
        visible = self.page.get_by_text("Start a new kernel", exact=True).is_visible()
        logger.info(f"Kernel popup visible: {visible}")
        return visible

    def reset_workspace(self):
        """Reset the Jupyterlab workspace.

        * Closes all Tabs & handle possible popups for saving changes,
        * make sure any kernel popups are dealt with
        * reset file browser is reset to root
        * Finally, ensure that the Launcher screen is showing
        """
        logger.info(">>> Reset JupyterLab workspace")

        # server is already running and there is no popup
        logger.info("Checking for kernel popup")
        popup = self._check_for_kernel_popup()

        # server is on running and there is a popup
        if popup:
            self._set_environment_via_popup(kernel=None)

        # go to Kernel menu
        kernel_menuitem = self.page.get_by_label("main menu").get_by_text(
            "Kernel", exact=True
        )
        kernel_menuitem.click()

        # shut down multiple running kernels
        with contextlib.suppress(Exception):
            print("Shutting down all kernels")
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
            self.page.get_by_role("button", name="Save", exact=True).click()

        self.page.get_by_title("VS Code [↗]").wait_for(state="visible")

        # Asset that the theme is set to JupyterLab Dark
        expect(
            self.page.get_by_text(
                "Set Preferred Dark Theme: JupyterLab Dark", exact=True
            )
        ).to_be_hidden()

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
            # if no kernel button exists
            logger.info("No kernel selected")
            if (
                no_kernel_button := self.page.get_by_role("dialog").get_by_role(
                    "button", name="No Kernel"
                )
                and no_kernel_button.is_visible()
            ):
                logger.info("No kernel button exists")
                no_kernel_button.click()
            else:
                # cancel operation
                try:
                    self.page.get_by_role("button", name="Cancel").click()
                    logger.info("Cancel button clicked")
                except Exception:
                    raise ValueError("Unable to escape kernel selection dialog.")
        else:
            # set the environment
            # failure here indicates that the environment doesn't exist either
            # because of incorrect naming syntax or because the env is still
            # being built
            kernel_selector = self.page.get_by_text(kernel, exact=True).nth(1)
            logger.info(f"Setting kernel to {kernel}")
            if kernel_selector.is_visible():
                logger.info("Kernel selector is visible")
                kernel_selector.click()

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
        logger.info(f"Kernel popup visible: {popup}")
        # if there is not a kernel popup, make it appear
        if not popup:
            self.page.get_by_role("menuitem", name="Kernel").click()
            self.page.get_by_role("menuitem", name="Change Kernel…").get_by_text(
                "Change Kernel…"
            ).click()

        # Wait for popup to show up
        self.page.get_by_role("heading", name="Start a new kernel").wait_for(
            state="visible"
        )
        logger.info("Kernel popup is visible")
        self._set_environment_via_popup(kernel)

        # wait for the jupyter UI to catch up before moving forward
        # see if the jupyter notebook label for the conda env is visible
        kernel_label_loc = self.page.get_by_role("button", name=kernel)
        logger.info(f"Kernel label is visible: {kernel_label_loc.is_visible()}")
        if not kernel_label_loc.is_visible():
            kernel_label_loc.wait_for(state="attached")

    def open_terminal(self):
        """Open Terminal in the Nebari Jupyter Lab"""
        self.page.get_by_text("File", exact=True).click()
        self.page.get_by_text("New", exact=True).click()
        self.page.get_by_role("menuitem", name="Terminal").get_by_text(
            "Terminal"
        ).click()

    def run_terminal_command(self, command):
        """Run a command on the terminal in the Nebari Jupyter Lab

        Parameters
        ----------
        command: str
            command to run in the terminal
        """
        self.page.get_by_role("textbox", name="Terminal input").fill(command)
        self.page.get_by_role("textbox", name="Terminal input").press("Enter")

    def write_file(self, filepath, content):
        """Write a file to Nebari instance filesystem

        The terminal is a blackbox for the browser. We can't access any of the
        displayed text, therefore we have no way of knowing if the commands
        are done executing. For this reason, there is an unavoidable sleep
        here that prevents playwright from moving on to ensure that the focus
        remains on the Terminal until we are done issuing our commands.

        Parameters
        ----------
        filepath: str
            path to write the file on the nebari file system
        content: str
            text to write to that file.
        """
        start = dt.datetime.now()
        logger.debug(f"Writing notebook to {filepath}")
        self.open_terminal()
        self.run_terminal_command(f"cat <<EOF >{filepath}")
        self.run_terminal_command(content)
        self.run_terminal_command("EOF")
        self.run_terminal_command(f"ls {filepath}")
        logger.debug(f"time to complete {dt.datetime.now() - start}")
        time.sleep(2)


# class Notebook:
#     def __init__(self, navigator: Navigator):
#         self.nav = navigator
#         self.nav.initialize

#     def run(
#         self,
#         path: str,
#         expected_outputs: List[str],
#         conda_env: str,
#         timeout: float = 1000,
#         completion_wait_time: float = 2,
#         retry: int = 2,
#         retry_wait_time: float = 5,
#         exact_match: bool = True,
#     ):
#         """Run a Jupyter notebook and check for expected output text.

#         This function will look for an exact match of expected_output_text
#         anywhere on the page, so ensure that your text is unique.

#         Parameters
#         ----------
#         path: str
#             Path to the notebook relative to the root of the JupyterLab instance.
#         expected_outputs: List[str]
#             Text to look for in the output of the notebook. This can be a
#             substring of the actual output if exact_match is False.
#         conda_env: str
#             Name of the conda environment. Python conda environments have the
#             structure "conda-env-nebari-git-nebari-git-dashboard-py" where
#             the actual name of the environment is "dashboard".
#         timeout: float
#             Time in seconds to wait for the expected output text to appear.
#             Default is 1000.
#         completion_wait_time: float
#             Time in seconds to wait between checking for expected output text.
#             Default is 2.
#         retry: int
#             Number of times to retry running the notebook.
#             Default is 2.
#         retry_wait_time: float
#             Time in seconds to wait between retries.
#             Default is 5.
#         exact_match: bool
#             If True, the expected output must match exactly. If False, the
#             expected output must be a substring of the actual output.
#             Default is True.
#         """
#         logger.debug(f">>> Running notebook: {path}")
#         filename = Path(path).name

#         # Navigate to specific notebook
#         logger.info(f"Opening notebook: {filename}")
#         self.open_notebook(path)
#         logger.info(f"Selecting notebook tab: {filename}")
#         self._select_notebook_tab(filename)
#         logger.info(f"Setting conda environment: {conda_env}")
#         self.nav.set_environment(kernel=conda_env)
#         logger.info(f"Restarting and running all cells")
#         self._select_notebook_tab(filename)

#         for _ in range(retry):
#             self._restart_run_all()
#             time.sleep(retry_wait_time)
#             logger.info(f"Waiting for commands to complete")
#             self._wait_for_commands_completion(timeout, completion_wait_time)
#             all_outputs = self._get_outputs()
#             logger.info(f"Checking outputs: {all_outputs}")
#             assert_match_all_outputs(expected_outputs, all_outputs, exact_match)

#     def create_notebook(self, conda_env=None):
#         self._open_file_menu()
#         self._select_submenu(0)
#         self._create_new_notebook()
#         self.nav.set_environment(kernel=conda_env)

#     def open_notebook(self, path: str):
#         self._open_file_menu()
#         self.nav.page.get_by_role("menuitem", name="Open from Path…").get_by_text(
#             "Open from Path…"
#         ).click()
#         self.nav.page.get_by_placeholder("/path/relative/to/jlab/root").fill(path)
#         self.nav.page.get_by_role("button", name="Open", exact=True).click()
#         self.nav.page.wait_for_load_state("networkidle")

#         if self.nav.page.get_by_text("Could not find path:", exact=False).is_visible():
#             logger.debug("Path to notebook is invalid")
#             raise RuntimeError("Path to notebook is invalid")

#     def assert_code_output(
#         self,
#         code: str,
#         expected_output: str,
#         timeout: float = 1000,
#         completion_wait_time: float = 2,
#         exact_match: bool = True,
#     ):
#         """Run code in the last cell and check for expected output text.

#         Parameters
#         ----------
#         code: str
#             Code to run in the last cell.
#         expected_output: str
#             Text to look for in the output of the notebook.
#         timeout: float
#             Time in seconds to wait for the expected output text to appear.
#             Default is 1000.
#         completion_wait_time: float
#             Time in seconds to wait between checking for expected output text.
#         """
#         self.run_in_last_cell(code)
#         self._wait_for_commands_completion(timeout, completion_wait_time)
#         outputs = self._get_outputs()
#         actual_output = outputs[-1] if outputs else ""
#         assert_match_output(expected_output, actual_output, exact_match)

#     def run_in_last_cell(self, code: str):
#         self._create_new_cell()
#         cell = self._get_last_cell()
#         cell.click()
#         cell.type(code)
#         time.sleep(1)
#         cell.press("Shift+Enter")
#         time.sleep(0.5)

#     def _create_new_cell(self):
#         new_cell_button = self.nav.page.query_selector(
#             'button[data-command="notebook:insert-cell-below"]'
#         )
#         new_cell_button.click()

#     def _get_last_cell(self):
#         cells = self.nav.page.locator(".CodeMirror-code").all()
#         for cell in reversed(cells):
#             if cell.is_visible():
#                 return cell
#         raise ValueError("Unable to get last cell")

#     def _wait_for_commands_completion(
#         self, timeout: float, completion_wait_time: float
#     ):
#         """Wait for commands to finish running.

#         Parameters
#         ----------
#         timeout: float
#             Time in seconds to wait for the expected output text to appear.
#         completion_wait_time: float
#             Time in seconds to wait between checking for expected output text.
#         """
#         elapsed_time = 0.0
#         start_time = time.time()
#         while elapsed_time < timeout:
#             running = self.nav.page.get_by_text("[*]").all()
#             still_visible = any(list(map(lambda r: r.is_visible(), running)))
#             if not still_visible:
#                 break
#             elapsed_time = time.time() - start_time
#             time.sleep(completion_wait_time)
#         if still_visible:
#             raise ValueError(
#                 f"Timeout: Commands did not finish within {timeout} seconds"
#             )

#     def _get_outputs(self) -> List[str]:
#         output_elements = self.nav.page.query_selector_all(".jp-OutputArea-output")
#         return [element.text_content().strip() for element in output_elements]

#     def _restart_run_all(self):
#         self.nav.page.get_by_role("menuitem", name="Kernel", exact=True).click()
#         self.nav.page.get_by_role(
#             "menuitem", name="Restart Kernel and Run All Cells…"
#         ).get_by_text("Restart Kernel and Run All Cells…").click()
#         restart_dialog_button = self.nav.page.get_by_role(
#             "button", name="Confirm Kernel Restart"
#         )
#         if restart_dialog_button.is_visible():
#             restart_dialog_button.click()

#     def _select_notebook_tab(self, filename: str):
#         self.nav.page.get_by_role("tab", name=filename).get_by_text(filename).click()

#     def _open_file_menu(self):
#         file_locator = self.nav.page.get_by_text("File", exact=True)
#         file_locator.wait_for(
#             timeout=self.nav.wait_for_server_spinup,
#             state="attached",
#         )
#         file_locator.click()

#     def _select_submenu(self, index: int):
#         submenu = self.nav.page.locator('[data-type="submenu"]').all()
#         submenu[index].click()

#     def _create_new_notebook(self):
#         self.nav.page.get_by_role("menuitem", name="Notebook").get_by_text(
#             "Notebook", exact=True
#         ).click()
#         self.nav.page.wait_for_load_state("networkidle")


# def assert_match_output(
#     expected_output: str, actual_output: str, exact_match: bool
# ) -> None:
#     """Assert that the expected_output is found in the actual_output.

#     Parameters
#     ----------
#     expected_output: str
#         The expected output text or regular expression to find in the
#         actual output.
#     actual_output: str
#         The actual output text to search for the expected output.
#     exact_match: bool
#         If True, then the expected_output must match the actual_output
#         exactly. Otherwise, the expected_output must be found somewhere in
#         the actual_output.
#     """
#     regex = re.compile(rf"{expected_output}")
#     match = (
#         regex.fullmatch(actual_output) if exact_match else regex.search(actual_output)
#     )
#     assert (
#         match is not None
#     ), f"Expected output: {expected_output} not found in actual output: {actual_output}"


# def assert_match_all_outputs(
#     expected_outputs: List[str],
#     actual_outputs: List[str],
#     exact_matches: Union[bool, List[bool]],
# ) -> None:
#     """Assert that the expected_outputs are found in the actual_outputs.

#     Parameters
#     ----------
#     expected_outputs: List[str]
#         A list of expected output text or regular expression to find in
#         the actual output.
#     actual_outputs: List[str]
#         A list of actual output text to search for the expected output.
#     exact_matches: Union[bool, List[bool]]
#         If True, then the expected_output must match the actual_output
#         exactly. Otherwise, the expected_output must be found somewhere in
#         the actual_output. If a list is provided, then it must be the same
#         length as expected_outputs and actual_outputs.
#     """
#     if isinstance(exact_matches, bool):
#         exact_matches = [exact_matches] * len(expected_outputs)

#     for expected_output, actual_output, exact in zip(
#         expected_outputs, actual_outputs, exact_matches
#     ):
#         assert_match_output(expected_output, actual_output, exact)
