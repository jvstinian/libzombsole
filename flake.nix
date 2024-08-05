{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/nixos-23.11";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };
  outputs = { nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system:
    let
      python_opencv_overlay = final: prev: {
          pythonPackagesOverlays = (prev.pythonPackagesOverlays or [ ]) ++ [
              (python-final: python-prev: {
                  opencv4 = python-prev.opencv4.override { enablePython = true; enableGtk2 = true; enableGtk3 = true; };
              })
          ];

          python310 = let
                  self = prev.python310.override {
                      inherit self;
                      packageOverrides = prev.lib.composeManyExtensions final.pythonPackagesOverlays;
                  }; 
              in self;

          python310Packages = final.python310.pkgs;
      };

      pkgs = import nixpkgs {
        inherit system;
        overlays = [ python_opencv_overlay ];
      };

      jvstinian-zombsole = pkgs.python310Packages.buildPythonPackage rec {
          name = "libzombsole";
          version = "0.3.1";

          src = ./.;

          propagatedBuildInputs = with pkgs.python310.pkgs; [
            docopt termcolor pillow opencv4 # tkinter
          ];

          dependencies = with pkgs.python310.pkgs; [
            docopt termcolor # tkinter
          ];

          nativeCheckInputs = with pkgs.python310.pkgs; [
            gym # requests flask docopt termcolor # tkinter # is pip required?
          ];

          doCheck = true; # tests failing

          meta = {
            homepage = "https://github.com/jvstinian/libzombsole";
            description = "Description here.";
            license = pkgs.lib.licenses.mit;
            maintainers = [ "jvstinian" ];
          };
      };
      my-python-packages = ps: with ps; [
          docopt
          termcolor
          # numpy
          opencv4
          gym
          jvstinian-zombsole
          # python-lsp-server
          # tkinter
          pip # TODO
      ];
      # my-python = jvstinian-zombsole.dependencies ++ (pkgs.python310.withPackages my-python-packages);
      my-python = pkgs.python310.withPackages my-python-packages;
    in rec {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
          my-python # python310.pkgs.pip # python310Packages.pip
        ];
      };
      packages = {
        zombsole = jvstinian-zombsole;
        default = jvstinian-zombsole;
      };
      apps.default = {
        type = "app";
        program = "${packages.zombsole}/bin/zombsole";
      };
    }
  );
}
