# Change name: cost-report.py

import json
import logging
import os
import pathlib
import re
import subprocess

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


def _check_infracost():
    try:
        subprocess.check_output(["infracost", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def _check_infracost_api_key():
    try:
        subprocess.check_output(["infracost", "configure", "get", "api_key"])
        return True
    except subprocess.CalledProcessError:
        return False


def _run_infracost(path):
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
        # return json.dumps(infracost_data)
        return infracost_data
    except subprocess.CalledProcessError:
        return None


def create_infracost_report(subparser):
    # TODO: Make the path configurable
    TF_PATH = "./stages/"
    if _check_infracost() and _check_infracost_api_key():
        if not os.path.exists(TF_PATH):
            print("Deployment is not available")
        else:
            data = _run_infracost(TF_PATH)

            # TODO: Customize the view of the table
            cost_table = Table(title="Cost Breakdown")
            cost_table.add_column("Name", justify="right", style="cyan", no_wrap=True)
            cost_table.add_column("Cost", justify="right", style="cyan", no_wrap=True)

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
                "Total Detected Costs", str(data["summary"]["totalDetectedResources"])
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
            print("Access the dashboard here: %s" % data["shareUrl"])
    else:
        print("Infracost is not installed or API key is not configured")


import json
import logging
import os
import pathlib
import re
import subprocess

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


def _check_infracost():
    try:
        subprocess.check_output(["infracost", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def _check_infracost_api_key():
    try:
        subprocess.check_output(["infracost", "configure", "get", "api_key"])
        return True
    except subprocess.CalledProcessError:
        return False


def _run_infracost(path):
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
        # return json.dumps(infracost_data)
        return infracost_data
    except subprocess.CalledProcessError:
        return None


def _check_directory_path(path):
    if os.path.exists(path):
        return True
    else:
        return False


def create_infracost_report(subparser):
    TF_PATH = "./stages/"
    if _check_infracost() and _check_infracost_api_key():
        if not os.path.exists(TF_PATH):
            print("Deployment is not available")
        else:
            data = _run_infracost(TF_PATH)

            cost_table = Table(title="Cost Breakdown")
            cost_table.add_column("Name", justify="right", style="cyan", no_wrap=True)
            cost_table.add_column("Cost", justify="right", style="cyan", no_wrap=True)

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
                "Total Detected Costs", str(data["summary"]["totalDetectedResources"])
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
            print("Access the dashboard here: %s" % data["shareUrl"])
    else:
        print("Infracost is not installed or API key is not configured")
