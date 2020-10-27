let
  pkgs = import (builtins.fetchTarball {
    url = "https://github.com/costrouc/nixpkgs/archive/615562a001a035ee94afdb72f00d2f9256136715.tar.gz";
    sha256 = "0a0zapfflj7747zhp1cmk8j9zfcvbppnkqjicqypc872166k9jai";
  }) {};

  pythonPackages = pkgs.python3Packages;
in
pkgs.mkShell {
  buildInputs = [
    pkgs.terraform
    pkgs.doctl
    pkgs.kubectl
    pkgs.kubernetes-helm

    # dependencies
    pythonPackages.cloudflare
    pythonPackages.auth0-python
    pythonPackages.cookiecutter
    pythonPackages.pyyaml
    pythonPackages.pydantic

    # testing
    pythonPackages.pytest
    pythonPackages.black
    pythonPackages.flake8

    # docs
    pythonPackages.sphinx

    # distribute
    pythonPackages.twine
  ];

  shellHook = ''
    export CLOUDFLARE_TOKEN=$(gopass show www/cloudflare.com/qhub@quansight.com token-qhub-dev-edit)
    export AUTH0_DOMAIN=$(gopass show www/auth0.com/qhub@quansight.com domain)
    export AUTH0_CLIENT_ID=$(gopass show www/auth0.com/qhub@quansight.com client_id)
    export AUTH0_CLIENT_SECRET=$(gopass show www/auth0.com/qhub@quansight.com client_secret)
  '';
}
