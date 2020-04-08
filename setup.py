from setuptools import setup, find_packages

setup(
    name='qhub',
    version='0.1',
    description='Automatically set up JupyterHubs on cloud providers',
    url='https://github.com/quansight/qhub',
    license='3 Clause BSD',
    packages=find_packages(),
    python_requires=">=3.5",
    install_requires=[
        'cryptography',
        'apache-libcloud'
    ],
    entry_points={
        'console_scripts': ['qhub-tljh=qhub.tljh.__main__:cli_start']
    }
)
