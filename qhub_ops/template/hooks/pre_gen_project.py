import re
import sys

valid_project_name = r"[A-Za-z0-9\-_.]+"

PROJECT_NAME = "{{ cookiecutter.project_name }}"
ENDPOINT = "{{ cookiecutter.endpoint }}"

if not re.fullmatch(r"[A-Za-z0-9\-_.]+", PROJECT_NAME):
    print(
        'ERROR: The project name (%s) is not a valid project name. Please use only A-Z a-z 0-9 "-" "_" "."'
        % PROJECT_NAME
    )
    sys.exit(1)


if not re.fullmatch(r"[A-Za-z0-9.]+", ENDPOINT):  # naive hostname check
    print("ERROR: The endpoint (%s) is not valid" % PROJECT_NAME)
    sys.exit(1)
