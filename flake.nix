{
  description = "QHub";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
    nixpkgs-keycloak = { url = "github:costrouc/nixpkgs/python-keycloak"; };
  };

  outputs = inputs@{ self, nixpkgs, nixpkgs-keycloak, ... }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      pythonPackages = pkgs.python3Packages;

      keycloak = (import nixpkgs-keycloak { system = "x86_64-linux"; }).python3Packages.python-keycloak;

      propagatedDependencies = [
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
      ];

      devDependencies = [
        # development
        pythonPackages.pytest
        pythonPackages.black
        pythonPackages.flake8
        pythonPackages.sphinx

        # additional
        pkgs.minikube
        pkgs.k9s
      ];
    in {
      defaultApp.x86_64-linux = pythonPackages.buildPythonPackage {
        pname = "qhub";
        version = "latest";

        src = ./.;

        propagatedBuildInputs = propagatedDependencies;

        patchPhase = ''
          substituteInPlace setup.py \
            --replace "cookiecutter==1.7.2" "cookiecutter" \
            --replace "azure-identity==1.6.1" "azure-identity" \
            --replace "azure-mgmt-containerservice==16.2.0" "azure-mgmt-containerservice"
        '';

        doCheck = false;
      };

      devShell.x86_64-linux =
        pkgs.mkShell {
          buildInputs = propagatedDependencies ++ devDependencies;
        };
    };
}
