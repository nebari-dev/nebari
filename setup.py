from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='qhub_ops',
    version='0.1.0',
    description='Management of QHub on Cloud Infrastructure',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/quansight/qhub-ops',
    author='Quansight',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='aws gcp do qhub',
    packages=find_packages(),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4',
    install_requires=[
        "cookiecutter",
        "pyyaml",
        "cloudflare",
        "auth0-python"
    ],
    extras_require={
        'dev': [
            'flake8',
            'black',
            'twine',
            'pytest'
        ]
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'qhub-ops = qhub_ops.__main__:main',
        ],
    },
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/quansight/QHub',
        'Source': 'https://github.com/quansight/QHub',
    },
)
