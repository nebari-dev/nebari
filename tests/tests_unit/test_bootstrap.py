import os
import pathlib
from unittest.mock import patch

from _nebari.stages.bootstrap import gen_gitignore


class TestGenGitignore:
    """Test the gen_gitignore function."""

    def test_gen_gitignore_creates_file_when_not_exists(self, tmp_path):
        """Test that gen_gitignore returns gitignore content when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = gen_gitignore()

        assert pathlib.Path(".gitignore") in result
        assert "terraform.tfstate" in result[pathlib.Path(".gitignore")]
        assert "__pycache__" in result[pathlib.Path(".gitignore")]

    def test_gen_gitignore_skips_when_exists(self, tmp_path):
        """Test that gen_gitignore returns empty dict when .gitignore already exists."""
        with patch("pathlib.Path.exists", return_value=True):
            result = gen_gitignore()

        assert result == {}

    def test_gen_gitignore_content_format(self, tmp_path):
        """Test that gen_gitignore returns properly formatted content."""
        with patch("pathlib.Path.exists", return_value=False):
            result = gen_gitignore()

        content = result[pathlib.Path(".gitignore")]
        expected_patterns = [
            "# ignore terraform state",
            ".terraform",
            "terraform.tfstate",
            "terraform.tfstate.backup",
            ".terraform.tfstate.lock.info",
            "# python",
            "__pycache__",
        ]

        for pattern in expected_patterns:
            assert pattern in content

    def test_gen_gitignore_file_system_integration(self, tmp_path):
        """Test gen_gitignore behavior with actual file system."""
        # Change to tmp directory
        original_cwd = pathlib.Path.cwd()
        os.chdir(tmp_path)

        try:
            # Test when .gitignore doesn't exist
            result = gen_gitignore()
            assert pathlib.Path(".gitignore") in result

            # Create .gitignore file
            gitignore_path = tmp_path / ".gitignore"
            gitignore_path.write_text("existing content")

            # Test when .gitignore exists
            result = gen_gitignore()
            assert result == {}

        finally:
            # Restore original working directory
            os.chdir(original_cwd)
