import os
import yaml

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROVIDER = "{{ cookiecutter.provider }}"
ENVIRONMENTS = eval("{{ cookiecutter.environments }}")


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    if ENVIRONMENTS:
        os.makedirs('environments', exist_ok=True)
        for name, spec in ENVIRONMENTS.items():
            with open(f'environments/{name}', 'w') as f:
                yaml.dump(spec, f)

    if PROVIDER == "aws":
        remove_file("infrastructure/do.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "do":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/gcp.tf")
    elif PROVIDER == "gcp":
        remove_file("infrastructure/aws.tf")
        remove_file("infrastructure/do.tf")
