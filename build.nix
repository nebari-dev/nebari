{ pkgs ? import <nixpkgs> { }, pythonPackages ? pkgs.python3Packages }:

pythonPackages.buildPythonPackage {
  pname = "qhub";
  version = "master";

  src = ./.;

  propagatedBuildInputs = [
    pythonPackages.cloudflare
    pythonPackages.auth0-python
    pythonPackages.pyyaml
    pythonPackages.cookiecutter
    pythonPackages.pydantic
  ];

  checkInputs = [
    pythonPackages.black
    pythonPackages.flake8
    pythonPackages.pytest
  ];

  checkPhase = ''
    # black qhub --check

    # flake8

    # pytest
  '';
}
