{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts/";
    nix-systems.url = "github:nix-systems/default";
    katsuba.url = "github:vbe0201/katsuba";
    wizwad.url = "github:wizspoil/wizwad";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    nix-systems,
    katsuba,
    wizwad,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      debug = true;
      systems = import nix-systems;
      perSystem = {
        pkgs,
        system,
        self',
        ...
      }: let
        python = pkgs.python311;
        pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
        packageName = "piratepog";
      in {
        packages.${packageName} = python.pkgs.buildPythonPackage {
          src = ./.;
          pname = packageName;
          version = pyproject.tool.poetry.version;
          format = "pyproject";
          pythonImportsCheck = [packageName];
          nativeBuildInputs = [
            python.pkgs.poetry-core
          ];
          propagatedBuildInputs = with python.pkgs; [click];
          meta.mainProgram = packageName;
        };

        packages.default = self'.packages.${packageName};

        devShells.default = pkgs.mkShell {
          name = packageName;
          packages = with pkgs; [
            (poetry.withPlugins(ps: with ps; [poetry-plugin-up]))
            python
            just
            alejandra
            python.pkgs.black
            python.pkgs.isort
            python.pkgs.vulture

            katsuba.packages.${system}.default
            wizwad.packages.${system}.default
          ];
        };
      };
    };
}
