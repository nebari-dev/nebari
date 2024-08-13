import json
import logging
import os
import re
from pathlib import Path

import hcl2
from tqdm import tqdm

from _nebari.utils import deep_merge

# Configure logging
logging.basicConfig(level=logging.INFO)


class HelmChartIndexer:
    # Define regex patterns to extract variable names
    LOCAL_VAR_PATTERN = re.compile(r"local.(.*[a-z])")
    VAR_PATTERN = re.compile(r"var.(.*[a-z])")

    def __init__(self, stages_dir, skip_charts, debug=False):
        self.stages_dir = stages_dir
        self.skip_charts = skip_charts
        self.charts = {}
        self.logger = logging.getLogger(__name__)

    def get_filepaths_that_contain_helm_release(self):
        """Get list of helm charts from nebari code-base"""
        # using pathlib to get list of files in the project root dir, look for all .tf files that
        # contain helm_release
        path = Path(__file__).parent.parent.absolute()
        path_tree = path.glob(f"{self.stages_dir}/**/main.tf")
        paths = []
        for file in path_tree:
            with open(file) as f:
                contents = f.read()
                if "helm_release" in contents:
                    paths.append(file)
                else:
                    continue
        logging.info(f"Found {len(paths)} files that contain helm_release")
        return paths

    def _argument_contains_variable_hook(self, argument):
        if "local." in argument or "var." in argument:
            return True
        return False

    def _clean_var_name(self, var_name, var_type):
        """Clean variable name"""
        if var_type == "local":
            # $(local.var_name)
            return self.LOCAL_VAR_PATTERN.findall(var_name)[0]
        if var_type == "var":
            # $(var.var_name)
            return self.VAR_PATTERN.findall(var_name)[0]

    def _load_variable_value(self, argument, parent_contents):
        if "local." in argument:
            var_name = self._clean_var_name(argument, "local")
            for local in parent_contents.get("locals", {}):
                if var_name in local:
                    return local[var_name]
            else:
                raise ValueError(f"Could not find local variable {var_name}")
        if "var." in argument:
            var_name = self._clean_var_name(argument, "var")
            for var in parent_contents.get("variable", {}):
                if var_name in var:
                    return var[var_name]["default"]
            else:
                raise ValueError(f"Could not find variable {var_name}")

    def retrieve_helm_information(self, filepath):
        parent_path = Path(filepath).parent

        if parent_path.name in self.skip_charts:
            self.logger.debug(f"Skipping {parent_path.name}")
            return self.charts

        self.logger.debug(f"Processing {parent_path.name}")
        parent_contents = {}

        for file in parent_path.glob("**/*.tf"):
            if file.as_posix().endswith("configmaps.tf"):
                # It should be safe to skip configmaps.tf files as they are not used to define helm_release resources
                # This was included as an exception to avoid a parsing error: on services/jupyterhub/configmaps.tf at line 8, column 5.
                continue
            with open(file, "r") as f:
                parent_contents = deep_merge(parent_contents, hcl2.load(f))

        for resource in parent_contents.get("resource", {}):
            if "helm_release" not in resource:
                continue
            for release_name, release_attrs in resource.get("helm_release", {}).items():
                self.logger.debug(f"Processing helm_release {release_name}")
                chart_name = release_attrs.get("chart", "")
                chart_version = release_attrs.get("version", "")
                chart_repository = release_attrs.get("repository", "")

                if self._argument_contains_variable_hook(chart_version):
                    self.logger.debug(
                        f"Spotted {chart_version} in {chart_name} chart metadata"
                    )
                    chart_version = self._load_variable_value(
                        chart_version, parent_contents
                    )

                if self._argument_contains_variable_hook(chart_repository):
                    self.logger.debug(
                        f"Spotted {chart_repository} in {chart_name} chart metadata"
                    )
                    chart_repository = self._load_variable_value(
                        chart_repository, parent_contents
                    )

                self.logger.debug(
                    f"Name: {chart_name} Version: {chart_version} Repository: {chart_repository}"
                )

                self.charts[chart_name] = {
                    "version": chart_version,
                    "repository": chart_repository,
                }

        if not self.charts:
            self.logger.debug("Could not find any helm_release under module resources")

        return self.charts

    def generate_helm_chart_index(self):
        """
        Generate an index of helm charts by searching for helm_release resources in Terraform files.

        Returns:
            A dictionary where the keys are the names of the charts and the values are dictionaries containing the chart's
            version and repository.

        Raises:
            ValueError: If no helm charts are found in the Terraform files.
        """
        paths = self.get_filepaths_that_contain_helm_release()
        helm_charts = {}
        for path in paths:
            helm_information = self.retrieve_helm_information(path)
            helm_charts.update(helm_information)

        if not helm_charts:
            raise ValueError("No helm charts found in the Terraform files.")

        with open("helm_charts.json", "w") as f:
            json.dump(helm_charts, f)

        return helm_charts


def pull_helm_chart(chart_index: dict, skip_charts: list) -> None:
    """
    Pull helm charts specified in `chart_index` and save them in the `helm_charts` directory.

    Args:
        chart_index: A dictionary containing chart names as keys and chart metadata (version and repository)
            as values.
        skip_charts: A list of chart names to skip.

    Raises:
        ValueError: If a chart could not be found in the `helm_charts` directory after pulling.
    """
    chart_dir = Path("helm_charts")
    chart_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(chart_dir)

    for chart_name, chart_metadata in tqdm(
        chart_index.items(), desc="Downloading charts"
    ):
        chart_version = chart_metadata["version"]
        chart_repository = chart_metadata["repository"]

        if chart_name in skip_charts:
            continue

        os.system(f"helm repo add {chart_name} {chart_repository}")
        os.system(
            f"helm pull {chart_name} --version {chart_version} --repo {chart_repository} --untar"
        )

        chart_filename = Path(f"{chart_name}-{chart_version}.tgz")
        if not chart_filename.exists():
            raise ValueError(
                f"Could not find {chart_name}:{chart_version} directory in {chart_dir}."
            )

    print("All charts downloaded successfully!")
    # shutil.rmtree(Path(os.getcwd()).parent / chart_dir)


def add_workflow_job_summary(chart_index: dict):
    """
    Based on the chart index, add a summary of the workflow job to the action log.

    Args:
        chart_index (dict): A dictionary containing chart names as keys and chart metadata (version and repository)
            as values.
    """
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n\n## Helm Charts\n")
            for chart_name, chart_metadata in chart_index.items():
                chart_version = chart_metadata["version"]
                chart_repository = chart_metadata["repository"]
                f.write(f"- {chart_name} ({chart_version}) from {chart_repository}\n")


if __name__ == "__main__":
    # charts = generate_index_of_helm_charts()
    STAGES_DIR = "src/_nebari/stages"
    SKIP_CHARTS = ["helm-extensions"]

    charts = HelmChartIndexer(
        stages_dir=STAGES_DIR, skip_charts=SKIP_CHARTS
    ).generate_helm_chart_index()
    pull_helm_chart(charts, skip_charts=SKIP_CHARTS)
    add_workflow_job_summary(charts)
