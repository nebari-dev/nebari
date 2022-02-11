import typing

from pydantic import BaseModel

# Notes:
# - attempted to follow the approach taken in qhub/schema.py
# - file name/location will need to be updated
# - using pydantic gives us .json_schema() for free
# - if pydantic model classes are made flexible enough, they can be reused


class GHA_on_push(BaseModel):
    branches: typing.List[str]
    path: typing.List[str]


class GHA_on(BaseModel):
    push: GHA_on_push


class GHA_jobs(BaseModel):
    pass


class QhubOps(BaseModel):
    name: str = "qhub auto update"
    on: GHA_on
    env: typing.Dict[str, str]
    jobs: GHA_jobs


# other experimentations below...
# some work and some don't


# from traitlets.config import Config

# def gen_cicd(config):
#     c = dict(
#             name = "qhub auto update",
#             on = dict(
#                 push = dict(
#                     branches = config["ci_cd"]["branch"],
#                     paths = "qhub-config.yaml"
#                 ),
#             ),
#         )
#     # c = Config(c)

#     return c

# import traitlets
# from traitlets.config import Config
# from traitlets.config.configurable import Configurable

# class QHUBOPS(Configurable):
#     name = traitlets.Unicode
#     on = traitlets.Dict(
#         push=traitlets.Dict(
#             branches=traitlets.Unicode,
#             paths=traitlets.Unicode,
#         ),
#     )

# def gen_qhub_ops(config_filename):
#     config_filename = pathlib.Path(config_filename)
#     with config_filename.open() as f:
#         yaml = YAML(typ="safe", pure=True)
#         config = yaml.load(f)

#     QhubOps = Config()
#     QhubOps.name = "qhub auto update"
#     # QhubOps.on.push
#     QhubOps.on.push.branches = config["ci_cd"]["branch"]
#     # QhubOps.on.push.paths = "qhub-config.yaml"

#     return QhubOps


# import jsonschema
# import traitlets

# valid_schema = dict(
#     name = "qhub auto update",
#     on = dict(
#         push = dict(
#             branches = str,
#             paths = "qhub-config.yaml",
#         ),
#     ),
# )

# class QhubOps(traitlets.HasTraits):

#     value = traitlets.Dict()

#     @traitlets.validate('value')
#     def _validate_value(self, proposal):
#         try:
#             jsonschema.validate(proposal['value'], valid_schema)
#         except jsonschema.ValidationError as e:
#             raise traitlets.TraitError(e)
#         return proposal['value']


# def generate_cicd_files(config_filename):
#     config_filename = pathlib.Path(config_filename)
#     with config_filename.open() as f:
#         yaml = YAML(typ="safe", pure=True)
#         config = yaml.load(f)
#     qhubops = QhubOps()

#     if config.get("ci_cd", None):
#         qhubops.value = dict(
#             on=dict(
#                 push=dict(
#                     branches=config["ci_cd"]["branch"]
#                 ),
#             ),
#         )

#     return qhubops.value
