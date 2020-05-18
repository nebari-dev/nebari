import pathlib

import flit
import setuptools
import toml

flit = toml.load("pyproject.toml")["tool"]["flit"]
metadata = flit["metadata"]

description, version = flit.common.get_docstring_and_version_via_import(
    flit.common.Module("poser")
)

setuptools.setup(
    name=metadata["module"],
    version=version,
    packages=setuptools.find_packages(),
    classifiers=metadata["classifiers"],
    url=metadata["home-page"],
    author=metadata["author"],
    install_requires=metadata.get("requires", []),
    author_email=metadata["author-email"],
    description=description,
    long_description=pathlib.Path(metadata["description-file"]).read_text(),
    long_description_content_type="text/markdown",
    extras_require=metadata.get("requires-extra", {}),
    # keywords=metadata.get('keywords', ),
    # console_scripts=metadata.get('scripts', []),
)
