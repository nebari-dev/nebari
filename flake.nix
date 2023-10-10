{
  description = "Nebari";

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
        pythonPackages.rich
        keycloak

        # cloud packages
        pythonPackages.azure-mgmt-containerservice
        pythonPackages.azure-identity
        pythonPackages.boto3
      ];

      devDependencies = [
        # development
        pythonPackages.pytest
        pythonPackages.pytest-timeout
        pythonPackages.black
        pythonPackages.sphinx
        pythonPackages.dask-gateway
        pythonPackages.paramiko
        pythonPackages.escapism
        pythonPackages.isort

        # additional
        pkgs.minikube
        pkgs.k9s
        pkgs.expect
      ];
    in rec {
      defaultApp.x86_64-linux = pythonPackages.buildPythonPackage {
        pname = "nebari";
        version = "latest";
        format = "pyproject";

        src = ./.;

        propagatedBuildInputs = propagatedDependencies;

        patchPhase = ''
          substituteInPlace setup.cfg \
            --replace "azure-identity==1.6.1" "azure-identity" \
            --replace "azure-mgmt-containerservice==16.2.0" "azure-mgmt-containerservice"
        '';

        doCheck = false;
      };

      devShell.x86_64-linux =
        pkgs.mkShell {
          buildInputs = propagatedDependencies ++ devDependencies ++ [ defaultApp.x86_64-linux ];
        };
    };
}
