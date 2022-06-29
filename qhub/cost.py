import json
import logging
import os
import re
import subprocess

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

logger = logging.getLogger(__name__)

INFRACOST_NOTE = """
QHub rely upon node-pools which is a usage resource but doesn't get captured in the above report. A general node-pool
will always have one node running will add quite an additional charge. Please check in with your cloud provider to see
the associated costs with node pools.

- Total Monthly Cost: The total monthly cost of the deployment of supported resources.
- Total Hourly Cost: The total hourly cost of the deployment of supported resources.
- Total Detected Costs: The total number of resources detected by Infracost.
- Total Supported Resources: The total number of resources supported by Infracost.
- Total Un-Supported Resources: The total number of resources unsupported by Infracost.
- Total Non-Priced Resources: The total number of resources that are not priced.
- Total Usage-Priced Resources: The total number of resources that are priced based on usage.
"""


def _check_infracost():
    """
    Check if infracost is installed
    """
    try:
        subprocess.check_output(["infracost", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def _check_infracost_api_key():
    """
    Check if infracost API key is configured
    """
    try:
        subprocess.check_output(["infracost", "configure", "get", "api_key"])
        return True
    except subprocess.CalledProcessError:
        return False


def _run_infracost(path):
    """
    Run infracost on the given path and return the JSON output
    """
    try:
        process = subprocess.Popen(
            ["infracost", "breakdown", "--path", path, "--format", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        infracost_data = json.loads(
            re.search("({.+})", stdout.decode("UTF-8"))
            .group(0)
            .replace("u'", '"')
            .replace("'", '"')
        )
        return infracost_data
    except subprocess.CalledProcessError:
        return None
    except AttributeError:
        return None


def _enable_infracost_dashboard():
    """
    Enable infracost dashboard
    """
    try:
        subprocess.check_output(
            ["infracost", "configure", "set", "enable_dashboard", "true"]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def infracost_report(path):
    """
    Generate a report of the infracost cost of the given path
    args:
        path: path to the qhub stages directory
    """
    if not path:
        path = os.path.join(os.getcwd(), "stages")

    if _check_infracost() and _check_infracost_api_key():
        _enable_infracost_dashboard()
        if not os.path.exists(path):
            logger.error("Deployment is not available")
        else:
            data = _run_infracost(path)
            if data:
                cost_table = Table(title="Cost Breakdown")
                cost_table.add_column(
                    "Name", justify="right", style="cyan", no_wrap=True
                )
                cost_table.add_column(
                    "Cost ($)", justify="right", style="cyan", no_wrap=True
                )

                cost_table.add_row("Total Monthly Cost", data["totalMonthlyCost"])
                cost_table.add_row("Total Hourly Cost", data["totalHourlyCost"])

                resource_table = Table(title="Resource Breakdown")
                resource_table.add_column(
                    "Name", justify="right", style="cyan", no_wrap=True
                )
                resource_table.add_column(
                    "Number", justify="right", style="cyan", no_wrap=True
                )

                resource_table.add_row(
                    "Total Detected Costs",
                    str(data["summary"]["totalDetectedResources"]),
                )
                resource_table.add_row(
                    "Total Supported Resources",
                    str(data["summary"]["totalSupportedResources"]),
                )
                resource_table.add_row(
                    "Total Un-Supported Resources",
                    str(data["summary"]["totalUnsupportedResources"]),
                )
                resource_table.add_row(
                    "Total Non-Priced Resources",
                    str(data["summary"]["totalNoPriceResources"]),
                )
                resource_table.add_row(
                    "Total Usage-Priced Resources",
                    str(data["summary"]["totalUsageBasedResources"]),
                )

                console = Console()
                console.print(cost_table)
                console.print(resource_table)
                console.print(f"Access the dashboard here: {data['shareUrl']}\n")
                console.print(Markdown(INFRACOST_NOTE))
            else:
                logger.error(
                    "No data was generated. Please check your QHub configuration and generated stages."
                )
    else:
        logger.error("Infracost is not installed or the API key is not configured")
