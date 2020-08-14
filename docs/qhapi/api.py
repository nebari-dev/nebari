from .schema import *

fastapi = __import__("fastapi").FastAPI()

# https://pydantic-docs.helpmanual.io/usage/types/


@fastapi.get("/yaml")
def to_yaml(app: Providers):
    return __import__("yaml").safe_dump(
        __import__("ujson").loads(Providers(**app).json()), default_flow_style=False
    )


@fastapi.get("/")
def hello():
    return {"hello": "world"}
