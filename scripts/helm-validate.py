import pathlib
import re

import hcl2

# 1. Get a list of paths whose files contains the helm_release resource
# 2. In each file, get the helm_release resource using the hcl2 library
# 3. Generate a JSON file with the following structure:
# { "chart_name": {"version" : "1.2.3", "repository": "https://charts.bitnami.com/bitnami"} }

STAGES_DIR = "nebari/template/stages"


def get_filepaths_that_contain_helm_release():
    """Get list of helm charts from nebari code-base"""
    # using pathlib to get list of files in the project root dir, look for all .tf files that
    # contain helm_release
    path = pathlib.Path(__file__).parent.parent.absolute()
    # print(path)
    path_tree = path.glob(f"{STAGES_DIR}/**/main.tf")
    paths = []
    for file in path_tree:
        # depending on the file, the resource might require extra information form locals or
        # variables, so we will just do a superficial check for now
        with open(file) as f:
            contents = f.read()
            # print(contents)
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


def process_chart_metadata(attrs):
    """Process chart metadata and return a dict"""
    chart_name = attrs.get("chart", "")
    chart_version = attrs.get("version", "")
    chart_repository = attrs.get("repository", "")

    # if chart_version is a variable, we need to get the value from locals or variables(?)
    for argument in [chart_version, chart_repository]:
        if _argument_contains_variable_hook(argument):
            print(f"Found variable in {chart_name} chart metadata")
            return {
                "version": chart_version,
                "repository": chart_repository,
                "possible_variable": argument,
                "name": chart_name,
            }
    else:
        return {"version": chart_version, "repository": chart_repository}


def get_helm_release_contents_from_hcl(filepath):
    """Load HCL file and parsed related helm_release resource"""
    # {
    #     "name": {"version": "", "repository": ""},
    # }
    helm_charts = {}
    with open(filepath, "r") as file:
        hcl = hcl2.load(file)
        for resource in hcl.get("resource", {}):
            try:
                for release_name, release_attrs in resource["helm_release"].items():
                    if release_name in ["prefect", "clearml", "custom-helm-deployment"]:
                        continue
                    chart_name = release_attrs.get("chart", "")
                    helm_charts[chart_name] = {
                        **process_chart_metadata(release_attrs),
                        "filepath": filepath.as_posix(),
                    }
            except KeyError:
                # print(f"No helm_release found for {filepath}")
                continue

    return helm_charts


def _clean_var_name(var_name, type):
    """Clean variable name"""
    if type == "local":
        # $(local.var_name)
        return re.match(r"\(local.(.*)\)", var_name).group(1)
    if type == "var":
        # $(var.var_name)
        return re.match(r"\(var.(.*)\)", var_name).group(1)


def post_process_charts(charts: list):
    """Post process charts that contain variables in their metadata"""
    for chart in charts:
        # name = chart["name"]
        parent_filepath = pathlib.Path(chart["filepath"]).parent
        parent_tree_contents = {}
        for file in parent_filepath.glob("**/*.tf"):
            with open(file, "r") as f:
                parent_tree_contents.update(hcl2.load(f))
        print(parent_tree_contents)
        # inspect locals and variables for the value of the variable
        # if helm_release.get(name):
        #     helm_resource = parent_tree_contents['resource']['helm_release'][helm_release]
        # chart_version = helm_resource['version']
        # if 'local.' in chart_version:
        #     local = set(item.get(_clean_var_name(chart_version, 'local'), None) for item in parent_tree_contents['locals'])[0]
        #     chart_version = local

        # if 'var.' in chart_version:
        #     var = set(item.get(_clean_var_name(chart_version, 'var'), None) for item in parent_tree_contents['variable'])[0]
        #     chart_version = var

        # chart_repository = helm_resource['repository']
        # if 'local.' in chart_repository:
        #     local = set(item.get(_clean_var_name(chart_repository, 'local'), None) for item in parent_tree_contents['locals'])[0]
        #     chart_repository = local

        # if 'var.' in chart_repository:
        #     var = set(item.get(_clean_var_name(chart_repository, 'var'), None) for item in parent_tree_contents['variable'])[0]
        #     chart_repository = var

        # print(f"Found {name} chart version: {chart_version} and repository: {chart_repository}")


if __name__ == "__main__":
    paths = get_filepaths_that_contain_helm_release()
    charts = {}
    for path in paths:
        charts.update(get_helm_release_contents_from_hcl(path))
    needs_post_processing = []
    for chart_name, chart_attrs in charts.items():
        if "possible_variable" in chart_attrs:
            needs_post_processing.append(chart_attrs)
    post_process_charts(needs_post_processing)

# def get_filepaths_that_contain_helm_release():
#     """Get list of helm charts from nebari code-base"""
#     # using pathlib to get list of files in the project root dir, look for all .tf files that contain helm_release
#     path = pathlib.Path(__file__).parent.parent.absolute()
#     # print(path)
#     path_tree = path.glob('nebari/template/stages/**/*.tf')
#     paths = []
#     for file in path_tree:
#         load_hcl_file(file)
#         # with open(file) as f:
#         #     contents = f.read()
#         # if "helm_release" in contents:
#         #     # print(file)
#         #     # print("###############################################")
#         #     paths.append(file)
#     print(f"Found {len(paths)} files that contain helm_release")
#     return paths

# def get_parent_dir(filepath):
#     """Get parent directory of a file"""
#     return pathlib.Path(filepath).parent

# def filter_paths_retrieve_parent_dir(paths):
#     """Filter paths and retrieve parent directory"""
#     filtered_paths = set()
#     for path in paths:
#         filtered_paths.add(get_parent_dir(path))
#     return filtered_paths

# def load_hcl_file(filepath):
#     with open(filepath, 'r') as file:
#         hcl = hcl2.load(file)
#         local = hcl.get('locals', {})
#         resource = hcl.get('resource', {})
#         for resource in hcl['resource']:
#             # print(resource)
#             try:
#                 if 'helm_release' in resource.keys():
#                     helm_release = resource['helm_release']
#                     for release_name, values in helm_release.items():
#                         # print("###############################################")
#                         print(f"Release name: {release_name}")
#                         print(f"Chart name: {values.get('chart', '')}")
#                         print(f"Chart version: {values.get('version', '')}")
#                         print(f"Chart repository: {values.get('repository', '')}")
#                         print("###############################################")
#                 else:
#                     return
#             except KeyError:
#                 print("No helm_release found in this file")
#                 print(filepath)
#                 print(hcl)

# def main():
#     """Main function"""
#     paths = get_filepaths_that_contain_helm_release()
# filtered_paths = filter_paths_retrieve_parent_dir(paths)
# for path in paths:
#     print(path)
#     load_hcl_file(path)


# def get_helm_chart_list():
#     """Get list of helm charts from nebari code-base"""
#     # using pathlib to get list of files in the project root dir, look for all .tf files that contain helm_release
#     path = pathlib.Path(__file__).parent.parent.absolute()
#     # print(path)
#     path_tree = path.glob('nebari/template/stages/**/*.tf')
#     with open(Path('/home/vcerutti/Quansight/Projects/Nebari/nebari/nebari/template/stages/07-kubernetes-services/modules/kubernetes/services/argo-workflows/main.tf'), 'r') as file:
#         hcl = hcl2.load(file)
#         local = hcl.get('locals', {})
#         resource = hcl.get('resource', {})
#         for resource in hcl['resource']:
#             pass
# if resource['helm_release']:
#     # print(resource['helm_release'])
# print("###############################################")
# for file in path_tree:
#     with open(file) as f:
#         contents = f.read()
#         if "helm_release" in contents:
#             print(file)
#             print(contents)
#             print("###############################################")
#             #matches = re.match(r"default = \"(?<currentValue>([0-9]+)\\.([0-9]+)\\.([0-9]+))\"\\n}\\n\\nvariable \".+_helm_chart_name\" {\\n.+\\n  default = \"(?<depName>[a-z].+)\"\\n}\\n\\n.+\\n.+\\n.+\\n}\\n\\nvariable \".+_helm_repository\" {\\n.+\\n  default = \"(?<registryUrl>.*?)\"", f.read())
#             # print(matches.groupdict())

# if __name__ == "__main__":
#     main()
