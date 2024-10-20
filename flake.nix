{
  inputs = {
    nixpkgs = {
      url = "github:nixos/nixpkgs/nixos-23.11";
    };
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };
  outputs = { nixpkgs, flake-utils, ... }: 
    let
      python-opencv-zombsole-overlay = final: prev: {
          pythonPackagesOverlays = (prev.pythonPackagesOverlays or [ ]) ++ [
              (python-final: python-prev: {
                  opencv4 = python-prev.opencv4.override { enablePython = true; enableGtk2 = true; enableGtk3 = true; };
              })
	      ] ++ [
              (python-final: python-prev: {
                  # jvstinian-zombsole = final.python310Packages.buildPythonPackage rec {
                  jvstinian-zombsole = python-final.buildPythonPackage rec {
                      name = "libzombsole";
                      src = ./.;
    
                      # was previously using "dependencies" but the packages 
                      # didn't appear to propagate to the output package
                      # propagatedBuildInputs = with final.python310.pkgs; [
                      propagatedBuildInputs = with python-final; [
                        docopt termcolor pillow opencv4 gym
                      ];
    
                      doCheck = true;
                      # Including pytestCheckHook in nativeCheckInputs to run pytest. 
                      # If needed, arguments can be passed to pytest using pytestFlagsArray.  
                      # Alternatively, checkPhase can be explicitly provided.
                      # See https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#using-pytestcheckhook 
                      # for more details.
                      # nativeCheckInputs = with final.python310.pkgs; [
                      nativeCheckInputs = with python-final; [
                        pytestCheckHook 
                      ];
                  };
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
    in 
      flake-utils.lib.eachDefaultSystem (system:
        let 
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ python-opencv-zombsole-overlay ];
          };
    
          dev-python-packages = ps: with ps; [
              docopt
              termcolor
              numpy
              pillow
              opencv4
              gym
              jvstinian-zombsole
          ];
          dev-python = pkgs.python310.withPackages dev-python-packages;
      in rec {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            dev-python
          ];
        };
        packages = {
          zombsole = pkgs.python310Packages.jvstinian-zombsole;
          default = pkgs.python310Packages.jvstinian-zombsole;
        };
        apps.default = {
          type = "app";
          program = "${packages.zombsole}/bin/zombsole";
        };
        apps.zombsole-stdio-json = {
          type = "app";
          program = "${packages.zombsole}/bin/zombsole-stdio-json";
        };
      }
    ) // {
      overlays.default = python-opencv-zombsole-overlay;
    };
}
