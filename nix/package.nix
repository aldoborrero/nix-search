{
  pkgs,
}:

pkgs.python313.pkgs.buildPythonApplication {
  pname = "nix-search";
  version = "0.1.0";
  pyproject = true;

  src = ../.;

  build-system = with pkgs.python313.pkgs; [
    setuptools
    wheel
  ];

  dependencies = with pkgs.python313.pkgs; [
    requests
    rich
    click
  ];

  nativeCheckInputs = with pkgs.python313.pkgs; [
    mypy
    types-requests
  ];

  checkPhase = ''
    runHook preCheck

    # Run mypy type checking
    mypy src/nix_search --strict

    runHook postCheck
  '';

  meta = with pkgs.lib; {
    description = "CLI tool to search NixOS packages and options using search.nixos.org API";
    license = licenses.mit;
    maintainers = with maintainers; [ aldoborrero ];
    mainProgram = "nix-search";
  };
}
