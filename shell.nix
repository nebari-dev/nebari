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
    export CLOUDFLARE_TOKEN=$(gopass www/cloudflare.com/qhub@quansight.com token-qhub-dev-edit)
    export AUTH0_DOMAIN=$(gopass www/auth0.com/qhub@quansight.com domain)
    export AUTH0_CLIENT_ID=$(gopass www/auth0.com/qhub@quansight.com client_id)
    export AUTH0_CLIENT_SECRET=$(gopass www/auth0.com/qhub@quansight.com client_secret)

    export AWS_ACCESS_KEY_ID=$(gopass www/digitalocean.com/costrouchov@quansight.com qhub-terraform-state-spaces-access-key)
    export SPACES_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    export AWS_SECRET_ACCESS_KEY=$(gopass www/digitalocean.com/costrouchov@quansight.com qhub-terraform-state-spaces-secret-key)
    export SPACES_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    export DIGITALOCEAN_TOKEN=$(gopass www/digitalocean.com/costrouchov@quansight.com qhub-terraform)
    doctl kubernetes cluster kubeconfig save do-jupyterhub-dev
  '';
}
