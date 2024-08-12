import contextlib
import datetime as dt
import logging
import time

from playwright.sync_api import expect

from tests.common.navigator import ServerManager

logger = logging.getLogger()


class Notebook:
    def start(self, navigator):
        logger.info("Starting notebook manager...")
        self.nav = navigator
        self.page = self.nav.page

    def reset_workspace(self):
        """Reset the JupyterLab workspace."""
        logger.info(">>> Resetting JupyterLab workspace")

        # Check for and handle kernel popup
        if self._check_for_kernel_popup():
            self._handle_kernel_popup()

        # Shutdown all kernels
        self._shutdown_all_kernels()

        # Navigate back to root folder and close all tabs
        self._navigate_to_root_folder()
        self._close_all_tabs()

        # Ensure theme and launcher screen
        self._assert_theme_and_launcher()

    def set_environment(self, kernel):
        """Set environment for a Jupyter notebook."""
        if not self._check_for_kernel_popup():
            self._trigger_kernel_change_popup()

        self._handle_kernel_popup(kernel)
        self._wait_for_kernel_label(kernel)

    def write_file(self, filepath, content):
        """Write a file to the Nebari instance filesystem."""
        logger.debug(f"Writing file to {filepath}")
        self._open_terminal()
        self._execute_terminal_commands(
            [f"cat <<EOF >{filepath}", content, "EOF", f"ls {filepath}"]
        )
        time.sleep(2)

    def _check_for_kernel_popup(self):
        """Check if the kernel popup is open."""
        logger.info("Checking for kernel popup")
        self.page.wait_for_load_state()
        time.sleep(3)
        visible = self.page.get_by_text("Start a new kernel", exact=True).is_visible()
        logger.info(f"Kernel popup visible: {visible}")
        return visible

    def _handle_kernel_popup(self, kernel=None):
        """Handle kernel popup by selecting the appropriate kernel or dismissing the popup."""
        if kernel:
            self._select_kernel(kernel)
        else:
            self._dismiss_kernel_popup()

    def _trigger_kernel_change_popup(self):
        """Trigger the kernel change popup."""
        self.page.get_by_role("menuitem", name="Kernel").click()
        self.page.get_by_role("menuitem", name="Change Kernel…").click()
        self.page.get_by_role("heading", name="Start a new kernel").wait_for(
            state="visible"
        )
        logger.info("Kernel popup is visible")

    def _select_kernel(self, kernel):
        """Select a kernel from the popup."""
        logger.info(f"Selecting kernel: {kernel}")
        kernel_selector = self.page.get_by_text(kernel, exact=True).nth(1)
        if kernel_selector.is_visible():
            kernel_selector.click()

    def _dismiss_kernel_popup(self):
        """Dismiss the kernel selection popup."""
        logger.info("Dismissing kernel popup")
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

    def _wait_for_kernel_label(self, kernel):
        """Wait for the kernel label to be visible."""
        kernel_label_loc = self.page.get_by_role("button", name=kernel)
        if not kernel_label_loc.is_visible():
            kernel_label_loc.wait_for(state="attached")
        logger.info(f"Kernel label {kernel} is now visible")

    def _shutdown_all_kernels(self):
        """Shutdown all running kernels."""
        logger.info("Shutting down all kernels")
        kernel_menuitem = self.page.get_by_label("main menu").get_by_text(
            "Kernel", exact=True
        )
        kernel_menuitem.click()
        with contextlib.suppress(Exception):
            shut_down_all = self.page.get_by_text(
                "Shut Down All Kernels...", exact=True
            )
            shut_down_all.wait_for(timeout=300, state="attached")
            shut_down_all.click()
        kernel_menuitem.click()
        with contextlib.suppress(Exception):
            shut_down_current = self.page.get_by_text("Shut Down Kernel", exact=True)
            shut_down_current.wait_for(timeout=300, state="attached")
            shut_down_current.click()

    def _navigate_to_root_folder(self):
        """Navigate back to the root folder in JupyterLab."""
        logger.info("Navigating to root folder")
        self.page.get_by_title(f"/home/{self.username}", exact=True).locator(
            "path"
        ).click()

    def _close_all_tabs(self):
        """Close all open tabs in JupyterLab."""
        logger.info("Closing all tabs")
        self.page.get_by_text("File", exact=True).click()
        self.page.get_by_role("menuitem", name="Close All Tabs", exact=True).click()

        if self.page.get_by_text("Save your work", exact=True).is_visible():
            self.page.get_by_role("button", name="Don't Save", exact=True).click()

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


# You can add more methods from the original code as needed, following this pattern
