#!/usr/bin/env python
import json
import os
import sys
import subprocess

docker_image_cmd = ['docker', 'ps', '--format', '{{.Names}} {{.ID}}']
docker_images_output = subprocess.check_output(docker_image_cmd, encoding='utf-8')[:-1]
docker_images = {line.split()[0]: line.split()[1] for line in docker_images_output.split('\n')}

if 'minikube' not in docker_images:
    print('minikube docker image not running')
    sys.exit(1)

docker_inspect_cmd = ['docker', 'inspect', '--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', docker_images['minikube']]
address = subprocess.check_output(docker_inspect_cmd, encoding='utf-8')[:-1].split('.')

filename = os.path.expanduser('~/.minikube/profiles/minikube/config.json')
with open(filename) as f:
    data = json.load(f)

start_address, end_address = '.'.join(address[0:3] + ['100']), '.'.join(address[0:3] + ['150'])
print('Setting start=%s end=%s' % (start_address, end_address))
data['KubernetesConfig']['LoadBalancerStartIP'] = start_address
data['KubernetesConfig']['LoadBalancerEndIP'] = end_address

with open(filename, 'w') as f:
    json.dump(data, f)
