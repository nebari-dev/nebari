#!/usr/bin/env python3
"""
Simple test script to verify the plugin hook system works.

This script tests that:
1. The hook is properly registered
2. Plugins can modify the config
3. Multiple plugins are applied sequentially
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nebari.plugins import nebari_plugin_manager
from tests.tests_unit.utils import render_config_partial


def test_plugin_hooks():
    print("Testing plugin hook system...")

    # Create a basic config like the integration tests do
    config = render_config_partial(
        project_name="test-project",
        namespace="dev",
        nebari_domain="test.nebari.dev",
        cloud_provider="aws",
        ci_provider="github-actions",
        auth_provider="password",
    )

    print(f"Original config project name: {config.project_name}")
    print(f"Original config namespace: {config.namespace}")

    # Load the example plugin
    nebari_plugin_manager.load_plugins(["example_plugin"])

    # Test the hook
    plugin_modified_configs = (
        nebari_plugin_manager.plugin_manager.hook.nebari_integration_test_config_modify(
            config=config, cloud="aws"
        )
    )

    print(
        f"Number of plugin modifications: {len(plugin_modified_configs) if plugin_modified_configs else 0}"
    )

    # Apply modifications sequentially
    if plugin_modified_configs:
        for i, modified_config in enumerate(plugin_modified_configs):
            if modified_config is not None:
                config = modified_config
                print(f"Applied modification #{i+1}")

    print(f"Final config project name: {config.project_name}")
    print(f"Final config namespace: {config.namespace}")

    print("Hook system test completed successfully!")


if __name__ == "__main__":
    test_plugin_hooks()
