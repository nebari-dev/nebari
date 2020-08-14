from .api import fastapi

__import__("uvicorn").run(fastapi)
