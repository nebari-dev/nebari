##
# To build:
# docker build -t quansight/qhub-userinfo:4 .

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

RUN pip install python-keycloak

COPY ./main.py /app/main.py
