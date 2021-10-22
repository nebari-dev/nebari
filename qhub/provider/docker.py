import subprocess
import shutil
import json

from qhub.utils import timer, run_subprocess_cmd


class DockerException(Exception):
    pass


def check_docker():
    docker_path = shutil.which('docker')
    if docker_path is None:
        raise DockerException('docker command is not installed')
    return docker_path


def run_docker_subprocess(processargs, verbose=True, **kwargs):
    docker_path = check_docker()
    command = [docker_path] + processargs
    if run_subprocess_cmd(command, **kwargs):
        raise DockerException("Docker returned an error")


def inspect(name):
    docker_path = check_docker()
    output = subprocess.check_output([docker_path, 'inspect', name, '--format={{json .}}'], encoding='utf-8').strip()
    return json.loads(output)


def images():
    docker_path = check_docker()
    output = subprocess.check_output([docker_path, 'images', '--format={{json .}}'], encoding='utf-8').strip()
    if not output:
        return []
    return [json.loads(_) for _ in output.split('\n')]


def ps():
    docker_path = check_docker()
    output = subprocess.check_output([docker_path, 'ps', '--format={{json .}}'], encoding='utf-8').strip()
    if not output:
        return []
    return [json.loads(_) for _ in output.split('\n')]


def build(dockerfile_path, build_directory, name, tag, verbose=False):
    command = ['build', build_directory, f'--file={dockerfile_path}', f'--tag={name}:{tag}']
    run_docker_subprocess(command, prefix='docker')
