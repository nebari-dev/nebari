from setuptools import setup, find_packages
from os import path

root_dir = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(root_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

__version__ = None
exec(open(path.join(root_dir, "qhub/version.py")).read())  # Load __version__

setup(
    name="qhub",
    version=__version__,
    description="Management of QHub on Cloud Infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quansight/qhub",
    author="Quansight",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="aws gcp do azure qhub",
    packages=find_packages(),
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",
    install_requires=[
        "cookiecutter==1.7.2",
        "gitignore-parser==0.0.8",
        "ruamel.yaml==0.17.10",
        "cloudflare==2.8.15",
        "auth0-python==3.16.2",
        "pydantic==1.8.2",
        "pynacl==1.3.0",
        "bcrypt==3.1.7",
    ],
    extras_require={
        "dev": [
            "flake8==3.8.4",
            "black==20.8b1",
            "twine==3.4.1",
            "pytest==6.2.4",
            "diagrams==0.20.0",
            "jhub-client==0.1.4",
        ],
    },
    include_package_data=True,
    entry_points={"console_scripts": ["qhub = qhub.__main__:main"]},
    project_urls={
        "Bug Reports": "https://github.com/quansight/qhub",
        "Source": "https://github.com/quansight/qhub",
    },
)
