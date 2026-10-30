{
  description = "A simple Django development environment using uv2nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      # 1. Load your uv workspace from the local directory
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # 2. Generate overlays to build Python dependencies from wheels
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
      editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; };

      # 3. Build the core Python package set for each system architecture
      pythonSets = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3; # Uses the default Python version from nixpkgs
        in
        (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.wheel
            overlay
          ]
        )
      );
    in
    {
      # 4. Expose the devShells configuration
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          
          # Apply the editable configuration so local code modifications hot-reload
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;
          
          # Create the isolated virtual environment including default workspace dependencies
          virtualenv = pythonSet.mkVirtualEnv "django-dev-env" workspace.deps.default;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv          # Keeps the uv CLI tool available inside the shell
              pkgs.sqlite      # Includes SQLite natively for standard Django setups
            ];

            shellHook = ''
              echo "⚡ Django Development Shell Activated ⚡"
              echo "Run 'python manage.py runserver' to start your backend."
            '';
          };
        }
      );
    };
}

