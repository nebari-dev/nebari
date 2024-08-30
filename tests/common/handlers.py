import logging
import re
import time

from playwright.sync_api import expect

logger = logging.getLogger()


class JupyterLab:
    def __init__(self, navigator):
        logger.debug(">>> Starting notebook manager...")
        self.nav = navigator
        self.page = self.nav.page

    def reset_workspace(self):
        """Reset the JupyterLab workspace."""
        logger.debug(">>> Resetting JupyterLab workspace")

        # Check for and handle kernel popup
        logger.debug(">>> Checking for kernel popup")
        if self._check_for_kernel_popup():
            self._handle_kernel_popup()

        # Shutdown all kernels
        logger.debug(">>> Shutting down all kernels")
        self._shutdown_all_kernels()

        # Navigate back to root folder and close all tabs
        logger.debug(">>> Navigating to root folder and closing all tabs")
        self._navigate_to_root_folder()
        logger.debug(">>> Closing all tabs")
        self._close_all_tabs()

        # Ensure theme and launcher screen
        logger.debug(">>> Ensuring theme and launcher screen")
        self._assert_theme_and_launcher()

    def set_environment(self, kernel):
        """Set environment for a Jupyter notebook."""
        if not self._check_for_kernel_popup():
            self._trigger_kernel_change_popup()

        self._handle_kernel_popup(kernel)
        self._wait_for_kernel_label(kernel)

    def write_file(self, filepath, content):
        """Write a file to the Nebari instance filesystem."""
        logger.debug(f">>> Writing file to {filepath}")
        self._open_terminal()
        self._execute_terminal_commands(
            [f"cat <<EOF >{filepath}", content, "EOF", f"ls {filepath}"]
        )
        time.sleep(2)

    def _check_for_kernel_popup(self):
        """Check if the kernel popup is open."""
        logger.debug(">>> Checking for kernel popup")
        self.page.wait_for_load_state()
        time.sleep(3)
        visible = self.page.get_by_text("Select KernelStart a new").is_visible()
        logger.debug(f">>> Kernel popup visible: {visible}")
        return visible

    def _handle_kernel_popup(self, kernel=None):
        """Handle kernel popup by selecting the appropriate kernel or dismissing the popup."""
        if kernel:
            self._select_kernel(kernel)
        else:
            self._dismiss_kernel_popup()

    def _dismiss_kernel_popup(self):
        """Dismiss the kernel selection popup."""
        logger.debug(">>> Dismissing kernel popup")
        no_kernel_button = self.page.get_by_role("dialog").get_by_role(
            "button", name="No Kernel"
        )
        if no_kernel_button.is_visible():
            no_kernel_button.click()
        else:
            try:
                self.page.get_by_role("button", name="Cancel").click()
            except Exception:
                raise ValueError("Unable to escape kernel selection dialog.")

    def _shutdown_all_kernels(self):
        """Shutdown all running kernels."""
        logger.debug(">>> Shutting down all kernels")
        kernel_menu = self.page.get_by_role("menuitem", name="Kernel")
        kernel_menu.click()
        shut_down_all = self.page.get_by_role("menuitem", name="Shut Down All Kernels…")
        logger.debug(
            f">>> Shut down all kernels visible: {shut_down_all.is_visible()} enabled: {shut_down_all.is_enabled()}"
        )
        if shut_down_all.is_visible() and shut_down_all.is_enabled():
            shut_down_all.click()
            self.page.get_by_role("button", name="Shut Down All").click()
        else:
            logger.debug(">>> No kernels to shut down")

    def _navigate_to_root_folder(self):
        """Navigate back to the root folder in JupyterLab."""
        logger.debug(">>> Navigating to root folder")
        self.page.get_by_title(f"/home/{self.nav.username}", exact=True).locator(
            "path"
        ).click()

    def _close_all_tabs(self):
        """Close all open tabs in JupyterLab."""
        logger.debug(">>> Closing all tabs")
        self.page.get_by_text("File", exact=True).click()
        self.page.get_by_role("menuitem", name="Close All Tabs", exact=True).click()

        if self.page.get_by_text("Save your work", exact=True).is_visible():
            self.page.get_by_role(
                "button", name="Discard changes to file", exact=True
            ).click()

    def _assert_theme_and_launcher(self):
        """Ensure that the theme is set to JupyterLab Dark and Launcher screen is visible."""
        expect(
            self.page.get_by_text(
                "Set Preferred Dark Theme: JupyterLab Dark", exact=True
            )
        ).to_be_hidden()
        self.page.get_by_title("VS Code [↗]").wait_for(state="visible")

    def _open_terminal(self):
        """Open a new terminal in JupyterLab."""
        self.page.get_by_text("File", exact=True).click()
        self.page.get_by_text("New", exact=True).click()
        self.page.get_by_role("menuitem", name="Terminal").get_by_text(
            "Terminal"
        ).click()

    def _execute_terminal_commands(self, commands):
        """Execute a series of commands in the terminal."""
        for command in commands:
            self.page.get_by_role("textbox", name="Terminal input").fill(command)
            self.page.get_by_role("textbox", name="Terminal input").press("Enter")
            time.sleep(0.5)


class Notebook(JupyterLab):
    def __init__(self, navigator):
        logger.debug(">>> Starting notebook manager...")
        self.nav = navigator
        self.page = self.nav.page

    def _open_notebook(self, notebook_name):
        """Open a notebook in JupyterLab."""
        self.page.get_by_text("File", exact=True).click()
        self.page.locator("#jp-mainmenu-file").get_by_text("Open from Path…").click()

        expect(self.page.get_by_text("Open PathPathCancelOpen")).to_be_visible()

        # Fill notebook name into the textbox and click Open
        self.page.get_by_placeholder("/path/relative/to/jlab/root").fill(notebook_name)
        self.page.get_by_role("button", name="Open").click()
        if self.page.get_by_text("Could not find path:").is_visible():
            self.page.get_by_role("button", name="Dismiss").click()
            raise ValueError(f"Notebook {notebook_name} not found")

        # make sure that this notebook is one currently selected
        expect(self.page.get_by_role("tab", name=notebook_name)).to_be_visible()

    def _run_all_cells(self):
        """Run all cells in a Jupyter notebook."""
        self.page.get_by_role("menuitem", name="Run").click()
        run_all_cells = self.page.locator("#jp-mainmenu-run").get_by_text(
            "Run All Cells", exact=True
        )
        if run_all_cells.is_visible():
            run_all_cells.click()
        else:
            self.page.get_by_text("Restart the kernel and run").click()
            # Check if restart popup is visible
            restart_popup = self.page.get_by_text("Restart Kernel?")
            if restart_popup.is_visible():
                restart_popup.click()
                self.page.get_by_role("button", name="Confirm Kernel Restart").click()

    def _wait_for_commands_completion(
        self, timeout: float, completion_wait_time: float
    ):
        """
        Wait for commands to finish running

        Parameters
        ----------
        timeout: float
            Time in seconds to wait for the expected output text to appear.
        completion_wait_time: float
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
            time.sleep(completion_wait_time)
        if still_visible:
            raise ValueError(
                f"Timeout Waited for commands to finish, "
                f"but couldn't finish in {timeout} sec"
            )

    def _get_outputs(self):
        output_elements = self.nav.page.query_selector_all(".jp-OutputArea-output")
        text_content = [element.text_content().strip() for element in output_elements]
        return text_content

    def run_notebook(self, notebook_name, kernel):
        """Run a notebook in JupyterLab."""
        # Open the notebook
        logger.debug(f">>> Opening notebook: {notebook_name}")
        self._open_notebook(notebook_name)

        # Set environment
        logger.debug(f">>> Setting environment for kernel: {kernel}")
        self.set_environment(kernel=kernel)

        # Run all cells
        logger.debug(">>> Running all cells")
        self._run_all_cells()

        # Wait for commands to finish running
        logger.debug(">>> Waiting for commands to finish running")
        self._wait_for_commands_completion(timeout=300, completion_wait_time=5)

        # Get the outputs
        logger.debug(">>> Gathering outputs")
        outputs = self._get_outputs()

        return outputs

    def _trigger_kernel_change_popup(self):
        """Trigger the kernel change popup. (expects a notebook to be open)"""
        self.page.get_by_role("menuitem", name="Kernel").click()
        kernel_menu = self.page.get_by_role("menuitem", name="Change Kernel…")
        if kernel_menu.is_visible():
            kernel_menu.click()
            self.page.get_by_text("Select KernelStart a new").wait_for(state="visible")
            logger.debug(">>> Kernel popup is visible")
        else:
            pass

    def _select_kernel(self, kernel):
        """Select a kernel from the popup."""
        logger.debug(f">>> Selecting kernel: {kernel}")

        self.page.get_by_role("dialog").get_by_label("", exact=True).fill(kernel)

        # List of potential selectors
        selectors = [
            self.page.get_by_role("cell", name=re.compile(kernel, re.IGNORECASE)).nth(
                1
            ),
            self.page.get_by_role("cell", name=re.compile(kernel, re.IGNORECASE)).first,
            self.page.get_by_text(kernel, exact=True).nth(1),
        ]

        # Try each selector until one is visible and clickable
        # this is done due to the different ways the kernel can be displayed
        # as part of the new extension
        for selector in selectors:
            if selector.is_visible():
                selector.click()
                logger.debug(f">>> Kernel {kernel} selected")
                return

        # If none of the selectors match, dismiss the popup and raise an error
        self._dismiss_kernel_popup()
        raise ValueError(f"Kernel {kernel} not found in the list of kernels")

    def _wait_for_kernel_label(self, kernel):
        """Wait for the kernel label to be visible."""
        kernel_label_loc = self.page.get_by_role("button", name=kernel)
        if not kernel_label_loc.is_visible():
            kernel_label_loc.wait_for(state="attached")
        logger.debug(f">>> Kernel label {kernel} is now visible")


class CondaStore(JupyterLab):
    def __init__(self, navigator):
        self.page = navigator.page
        self.nav = navigator

    def _open_conda_store_service(self):
        self.page.get_by_text("Services", exact=True).click()
        self.page.get_by_text("Environment Management").click()
        expect(self.page.get_by_role("tab", name="conda-store")).to_be_visible()
        time.sleep(2)

    def _open_new_environment_tab(self):
        self.page.get_by_label("Create a new environment in").click()
        expect(self.page.get_by_text("Create Environment")).to_be_visible()

    def _assert_user_namespace(self):
        expect(
            self.page.get_by_role("button", name=f"{self.nav.username} Create a new")
        ).to_be_visible()

    def _get_shown_namespaces(self):
        _envs = self.page.locator("#environmentsScroll").get_by_role("button")
        _env_contents = [env.text_content() for env in _envs.all()]
        # Remove the "New" entry from each namespace "button" text
        return [
            namespace.replace(" New", "")
            for namespace in _env_contents
            if namespace != " New"
        ]

    def _assert_logged_in(self):
        login_button = self.page.get_by_role("button", name="Log in")
        if login_button.is_visible():
            login_button.click()
            # wait for page to reload
            self.page.wait_for_load_state()
            time.sleep(2)
            # A reload is required as conda-store "created" a new page once logged in
            self.page.reload()
            self.page.wait_for_load_state()
            self._open_conda_store_service()
        else:
            # In this case logout should already be visible
            expect(self.page.get_by_role("button", name="Logout")).to_be_visible()
        self._assert_user_namespace()

    def conda_store_ui(self):
        logger.debug(">>> Opening Conda Store UI")
        self._open_conda_store_service()

        logger.debug(">>> Assert user is logged in")
        self._assert_logged_in()

        logger.debug(">>> Opening new environment tab")
        self._open_new_environment_tab()
