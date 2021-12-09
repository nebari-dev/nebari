{
  description = "QHub";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
  };

  outputs = inputs@{ self, nixpkgs, ... }: {
    devShell.x86_64-linux =
      let
        pkgs = import nixpkgs { system = "x86_64-linux"; };
        pythonPackages = pkgs.python3Packages;
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
          # development
          pythonPackages.pytest
          pythonPackages.black
          pythonPackages.flake8
          pythonPackages.sphinx
        ];
      };
  };
}
