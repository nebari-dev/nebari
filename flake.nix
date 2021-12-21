{
  description = "QHub";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
    nixpkgs-keycloak = { url = "github:costrouc/nixpkgs/python-keycloak"; };
  };

  outputs = inputs@{ self, nixpkgs, nixpkgs-keycloak, ... }: {
    devShell.x86_64-linux =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };
        pythonPackages = pkgs.python3Packages;

        keycloak = (import nixpkgs-keycloak { system = "x86_64-linux"; }).python3Packages.python-keycloak;
      in pkgs.mkShell {
        buildInputs = [
          pythonPackages.cookiecutter
          pythonPackages.ruamel-yaml
          pythonPackages.cloudflare
          pythonPackages.auth0-python
          pythonPackages.pydantic
          pythonPackages.pynacl
          pythonPackages.bcrypt
          pythonPackages.kubernetes
          pythonPackages.packaging
          keycloak

          # cloud packages
          pythonPackages.azure-mgmt-containerservice
          pythonPackages.azure-identity
          pythonPackages.boto3

          # development
          pythonPackages.pytest
          pythonPackages.black
          pythonPackages.flake8
          pythonPackages.sphinx

          # additional
          pkgs.minikube
          pkgs.k9s
        ];
      };
  };
}
