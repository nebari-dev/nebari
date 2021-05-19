# Installation
## Pre-requisites
* QHub is supported by macOS and Linux operating systems.
  > NOTE: **Currently, QHub cannot be installed on Windows**.
* We recommend the adoption of virtual environments (`conda`, `pipenv` or `venv`) for successful usage. 

### Install QHub
QHub's installation can be performed by using:
* `conda`:
  ```bash
  conda install -c conda-forge qhub
  ```
  
* or `pip` (instead):
    ```bash
    pip install qhub
    ```  
Once finished, you can check QHub's version (and additional CLI args) by typing:
```bash
qhub --help
```
If successful, the CLI output will be similar to the following:
```bash
usage: qhub [-h] [-v] {deploy,destroy,render,init,validate,destroy} ...

QHub command line

positional arguments:
  {deploy,destroy,render,init,validate,destroy}
                        QHub - ||QHUB_VERSION||

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         QHub version
```
