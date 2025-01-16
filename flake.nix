{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      perSystem =
        { pkgs, ... }:
        {
          devShells.default = pkgs.mkShell {
            name = "roc-package-index-data";
            packages = [
              pkgs.actionlint
              pkgs.basedpyright
              pkgs.check-jsonschema
              pkgs.just
              pkgs.nixfmt-rfc-style
              pkgs.nodePackages.prettier
              pkgs.pre-commit
              pkgs.python3Packages.pre-commit-hooks
              (pkgs.python3.withPackages (python-pkgs: [
                python-pkgs.brotli
                python-pkgs.githubkit
                python-pkgs.httpx
                python-pkgs.msgspec
                # Dev
                python-pkgs.ssort
                # Nix
                python-pkgs.venvShellHook
              ]))
              pkgs.ratchet
              pkgs.ruff
            ];
            shellHook = "pre-commit install --overwrite";
          };
          formatter = pkgs.nixfmt-rfc-style;
        };
    };
}
