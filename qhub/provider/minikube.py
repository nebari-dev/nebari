import tempfile
import os
import sys
import urllib.request
import platform
import subprocess
import re
import json
import shutil

from qhub.utils import run_subprocess_cmd, QHubError, change_directory
from qhub import constants
from qhub.console import console


class MinikubeError(QHubError):
    pass


def _patch_nixos_minikube_binary(minikube_path):
    """Minikube binary has ld interpreter hardcoded

    Use patchelf to change the ld interpreter to one that works for NixOS
    """
    ls_command = shutil.which('ls')
    patchelf_command = shutil.which('patchelf')

    if sys.platform != 'linux' or 'NixOS' not in open('/etc/os-release').read():
        return

    command = [patchelf_command, '--print-interpreter', ls_command]
    interpreter = subprocess.check_output(command, encoding='utf-8')[:-1]

    command = [patchelf_command, '--set-interpreter', interpreter, minikube_path]
    subprocess.check_output(command)


def download_minikube_binary(version=constants.MINIKUBE_VERSION):
    os_mapping = {
        "linux": "linux",
        "win32": "windows",
        "darwin": "darwin",
        "freebsd": "freebsd",
        "openbsd": "openbsd",
        "solaris": "solaris",
    }

    architecture_mapping = {
        "x86_64": "amd64",
        "i386": "386",
        "armv7l": "arm",
        "aarch64": "arm64",
    }

    download_url = f"https://github.com/kubernetes/minikube/releases/download/v{version}/minikube-{os_mapping[sys.platform]}-{architecture_mapping[platform.machine()]}"
    filename_directory = os.path.join(tempfile.gettempdir(), "minikube", version)
    filename_path = os.path.join(filename_directory, "minikube")

    if not os.path.isfile(filename_path):
        os.makedirs(filename_directory, exist_ok=True)

        console.print(f"downloading and extracting minikube binary from url={download_url} to path={filename_path}")

        with urllib.request.urlopen(download_url) as resp:
            with open(filename_path, "wb") as f:
                f.write(resp.read())

    os.chmod(filename_path, 0o755)
    _patch_nixos_minikube_binary(filename_path)
    return filename_path


def run_minikube_subprocess(process_args, **kwargs):
    minikube_path = download_minikube_binary()
    command = [minikube_path] + process_args
    if run_subprocess_cmd([minikube_path] + process_args, **kwargs):
        raise MinikubeError("Minikube returned an error")


def version():
    minikube_path = download_minikube_binary()
    version_output = subprocess.check_output([minikube_path, "version"]).decode(
        "utf-8"
    )
    return re.search(r"minikube version: v(\d+\.\d+.\d+)", version_output).group(1)


def image_load(image, overwrite=True):
    minikube_path = download_minikube_binary()

    overwrite_command = '--overwrite=true' if overwrite else '--overwrite=false'
    command = ['image', 'load', overwrite_command, image]
    run_minikube_subprocess(command, prefix="minikube")


def image_build(dockerfile_path, build_directory, name, tag, verbose=False):
    command = ['image', 'build', f'--file={dockerfile_path}', f'--tag={name}:{tag}']
    with change_directory(build_directory):
        run_minikube_subprocess(command, prefix='minikube')


def start(driver='docker', memory='8g', cpu='2', profile="qhub", kubernetes_version=None):
    command = ["start", f"--driver={driver}", f"--memory={memory}", f"--cpus={cpu}", f"--profile={profile}"]

    if kubernetes_version:
        command = command + [f"--kubernetes-version={kubernetes_version}"]

    run_minikube_subprocess(command, prefix="minikube")


def status(profile="qhub"):
    minikube_path = download_minikube_binary()
    command = [minikube_path, "status", f"--profile={profile}"]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def delete(profile="qhub"):
    run_minikube_subprocess(["delete", "--profile", profile], prefix="minikube")


def addons_enable(addon, profile="qhub"):
    run_minikube_subprocess(["addons", "enable", addon, "--profile", profile], prefix="minikube")


def configure_metallb(profile="qhub", start_address=None, end_address=None):
    """Configure metallb load balancer

    Assumes that minikube docker image is running
    """
    docker_image_cmd = ['docker', 'ps', '--format', '{{.Names}} {{.ID}}']
    docker_images_output = subprocess.check_output(docker_image_cmd, encoding='utf-8')[:-1]
    docker_images = {line.split()[0]: line.split()[1] for line in docker_images_output.split('\n')}

    if profile not in docker_images:
        raise ValueError('minikube docker image not running')

    docker_inspect_cmd = ['docker', 'inspect', '--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', docker_images[profile]]
    address = subprocess.check_output(docker_inspect_cmd, encoding='utf-8')[:-1].split('.')

    filename = os.path.expanduser(f'~/.minikube/profiles/{profile}/config.json')
    with open(filename) as f:
        data = json.load(f)

    start_address, end_address = '.'.join(address[0:3] + ['100']), '.'.join(address[0:3] + ['150'])
    console.print(f"configuring MetalLB start={start_address} end={end_address}")
    data['KubernetesConfig']['LoadBalancerStartIP'] = start_address
    data['KubernetesConfig']['LoadBalancerEndIP'] = end_address

    with open(filename, 'w') as f:
        json.dump(data, f)
