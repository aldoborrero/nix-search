{ pkgs, perSystem }:
perSystem.devshell.mkShell {
  packages = (
    with pkgs;
    [
      python313
      just
      perSystem.self.formatter
    ]
  );

  env = [
    {
      name = "NIX_PATH";
      value = "nixpkgs=${toString pkgs.path}";
    }
    {
      name = "NIX_DIR";
      eval = "$PRJ_ROOT/nix";
    }
  ];

  commands = [
  ];
}
