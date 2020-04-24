import os

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROVIDER = "{{ cookiecutter.provider }}"


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    if PROVIDER == "aws":
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "do":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "gcp":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")
