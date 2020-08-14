let
  pkgs = import (builtins.fetchTarball {
    url = "https://github.com/costrouc/nixpkgs/archive/615562a001a035ee94afdb72f00d2f9256136715.tar.gz";
    sha256 = "0a0zapfflj7747zhp1cmk8j9zfcvbppnkqjicqypc872166k9jai";
  }) {};

  pythonPackages = pkgs.python3Packages;
in
pythonPackages.buildPythonPackage {
  pname = "qhub-kubernetes";
  version = "master";

  src = ./.;

  propagatedBuildInputs = [
    pythonPackages.cloudflare
    pythonPackages.auth0-python
    pythonPackages.pyyaml
    pythonPackages.cookiecutter
  ];

  checkInputs = [
    pythonPackages.black
    pythonPackages.flake8
    pythonPackages.pytest
  ];

  checkPhase = ''
    black qhub_ops --check

    flake8

    pytest
  '';
}
