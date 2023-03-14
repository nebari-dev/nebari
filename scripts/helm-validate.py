import pathlib
import re

import hcl2
from nebari.utils import deep_merge

# 1. Get a list of paths whose files contains the helm_release resource
# 2. In each file, get the helm_release resource using the hcl2 library
# 3. Generate a JSON file with the following structure:
# { "chart_name": {"version" : "1.2.3", "repository": "https://charts.bitnami.com/bitnami"} }

STAGES_DIR = "nebari/template/stages"
SKIP_CHARTS = ["prefect", "clearml", "helm-extensions"]
DEBUG = False

def get_filepaths_that_contain_helm_release():
    """Get list of helm charts from nebari code-base"""
    # using pathlib to get list of files in the project root dir, look for all .tf files that
    # contain helm_release
    path = pathlib.Path(__file__).parent.parent.absolute()
    path_tree = path.glob(f"{STAGES_DIR}/**/main.tf")
    paths = []
    for file in path_tree:
        # depending on the file, the resource might require extra information form locals or
        # variables, so we will just do a superficial check for now
        with open(file) as f:
            contents = f.read()
            if "helm_release" in contents:
                paths.append(file)
            else:
                continue
    print(f"Found {len(paths)} files that contain helm_release")
    return paths


def _argument_contains_variable_hook(argument):
    if "local." in argument:
        return True
    if "var." in argument:
        # we are checking this here but grabbing this value would be really difficult
        return True

def _clean_var_name(var_name, type):
    """Clean variable name"""
    if type == "local":
        # $(local.var_name)
        return re.findall(r"local.(.*[a-z])", var_name)[0]
    if type == "var":
        # $(var.var_name)
        return re.findall(r"var.(.*[a-z])", var_name)[0]

def _load_variable_value(argument, parent_contents):
    if "local." in argument:
        var_name = _clean_var_name(argument, "local")
        for local in parent_contents.get("locals", {}):
            if var_name in local:
                return local[var_name]
        else:
            raise ValueError(f"Could not find local variable {var_name}")
    if "var." in argument:
        var_name = _clean_var_name(argument, "var")
        for var in parent_contents.get("variable", {}):
            if var_name in var:
                return var[var_name]
        else:
            raise ValueError(f"Could not find variable {var_name}")


def retrieve_helm_information(filepath):
    print("###############################################")
    _charts = {}
    print("-- Initialize helm_release store chart resource") if DEBUG else None

    parent_path = pathlib.Path(filepath).parent

    if parent_path.name in SKIP_CHARTS:
        print(f"-- Skipping {parent_path.name}") if DEBUG else None
        return _charts

    print(f"-- Processing {parent_path.name}") if DEBUG else None
    parent_contents = {}
    for file in parent_path.glob("**/*.tf"):
        with open(file, "r") as f:
            parent_contents = deep_merge(parent_contents, hcl2.load(f))
        # loading all the relatives will give us the locals and variables in case we need them

    for resource in parent_contents.get("resource", {}):
        if "helm_release" not in resource:
            print(f"-- Skipping {resource.keys()} (not helm_release)") if DEBUG else None
            continue
        try:
            for release_name, release_attrs in resource["helm_release"].items():
                print(f"-- Processing helm_release {release_name}") if DEBUG else None
                chart_name = release_attrs.get("chart", "")
                chart_version = release_attrs.get("version", "")
                chart_repository = release_attrs.get("repository", "")
                # if chart_version is a variable, we need to get the value from locals or variables(?)
                if _argument_contains_variable_hook(chart_version):
                    print(f"-- Spotted {chart_version} in {chart_name} chart metadata") if DEBUG else None
                    chart_version = _load_variable_value(chart_version, parent_contents)

                if _argument_contains_variable_hook(chart_repository):
                    print(f"-- Spotted {chart_repository} in {chart_name} chart metadata") if DEBUG else None
                    chart_repository = _load_variable_value(chart_repository, parent_contents)

                print(f" Name: {chart_name} \n Version: {chart_version} \n Repository: {chart_repository}")

                _charts.update({chart_name : {"version": chart_version, "repository": chart_repository}})
        except KeyError:
            print(f"Could not find helm_release in {filepath} for")
            continue

    if not _charts:
        print(f"-- Could not find any helm_release under module resources") if DEBUG else None

    return _charts

def generate_index_of_helm_charts():
    """Generate index of helm charts"""
    paths = get_filepaths_that_contain_helm_release()
    helm_charts = {}
    for path in paths:
        helm_information = retrieve_helm_information(path)
        helm_charts.update(helm_information)
    with open("helm_charts.json", "w") as f:
        f.write(str(helm_charts))
    return helm_charts

def pull_helm_chart(chart_index : dict):
    """Pull helm chart"""
    import os
    print("Creating helm_charts directory")
    os.system("mkdir helm_charts && cd helm_charts")
    for chart_name, chart_metadata in chart_index.items():
        chart_version = chart_metadata["version"]
        chart_repository = chart_metadata["repository"]
        print(f"Adding {chart_name} repository")
        os.system(f"helm repo add {chart_name} {chart_repository}")

        print(f"Pulling {chart_name} chart")
        os.system(f"helm pull {chart_name} --version {chart_version} --repo {chart_repository} --untar --untardir helm_charts")

        print("Inspecting downloaded chart")
        if not os.path.exists(f"helm_charts/{chart_name}-{chart_version}.tgz"):
            raise f"Could not find {chart_name}:{chart_version} directory in helm_charts."
    print("All charts downloaded successfully, removing helm_charts directory")
    os.system("cd .. && rm -rf helm_charts")

if __name__ == "__main__":
    charts = generate_index_of_helm_charts()
    pull_helm_chart(charts)