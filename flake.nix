{
  description = "QHub Application and Environment";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.poetry2nix.url = "github:nlewo/poetry2nix/crypto-3.5";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          qhub = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
          };

          # The environment
          qhubEnv = prev.poetry2nix.mkPoetryEnv {
            projectDir = ./.;
          };
        })
      ];
    } // (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
      in
      rec {

        apps = {
          qhub = pkgs.qhub;
        };

        defaultApp = apps.qhub;

        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.qhubEnv ];
        };

        docs = pkgs.mkDerivation {
          src = ./docs;

          buildInputs = [
            pkgs.qhubEnv
          ];

          buildPhase = ''
            sphinx-build . build
          '';

          outputPhase = ''
            mkdir -p $out
            cp -r build/* $out
          '';
        };
      }));
}
