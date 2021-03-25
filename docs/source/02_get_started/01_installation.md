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
usage: qhub [-h] [-v] {deploy,render,init,validate,destroy} ...

QHub command line

positional arguments:
  {deploy,render,init,validate,destroy}
                        QHub Ops - 0.2.3

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         QHub Ops version
```
## Add-on
### Install Terraform
QHub runs Terraform on the background. Hence, you will need to manually install a compatible version of Terraform.
Currently, QHub is **ONLY** compatible with Terraform version 0.13.5.

To install using conda run:
```bash
conda install -c conda-forge terraform=0.13.5
```
Make sure that the location of the `terraform` bin file is added to your PATH. Not sure how to set path variables?
Take a look at [this Stack Overflow post](https://stackoverflow.com/questions/14637979/how-to-permanently-set-path-on-linux-unix).

OR manually install it:

1. Download the binary with URL by running `wget https://releases.hashicorp.com/terraform/0.13.5/`
2. Add it to `~/.local/bin`
3. Add file to your path by running `export PATH=$HOME/.local/bin:$PATH`.


In case you need a more detailed explanation, watch the
[demo of the Terraform installation process](https://learn.hashicorp.com/tutorials/terraform/install-cli).
