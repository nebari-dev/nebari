# qhub frontend

This repo houses the qhub frontend moving forward. This effort will house a backend
written in fastAPI, and a fronend in Vue, with additional components.

`prototype` houses notebooks that have been used to prototype data

`app` houses the fastAPI backend

## Running with dockerfile

`docker build -t <image_name> .`

`docker run -d --name <container_name> -p 8444:8444 <image_name>`

## Running without dockerfile 

`cd` to `src` and run `python main.py`