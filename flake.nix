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
          myapp = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
          };

          # The environment
          myenv = prev.poetry2nix.mkPoetryEnv {
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
          myapp = pkgs.myapp;
        };

        defaultApp = apps.myapp;

        devShell = pkgs.mkShell {
          buildInputs = [ pkgs.myenv ];
        };
      }));
}
