{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        myPython = (
          pkgs.python3.withPackages (
            ps: with ps; [
              numpy
              matplotlib
              notebook
              pandas
              moderngl
              glfw
              pybind11
            ]
          )
        );
      in
      {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [
            myPython
            pkgs.libGL
            pkgs.libGLU
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.libGL}/lib:${pkgs.libGLU}/lib
            export CPATH=''${CPATH:+$CPATH:}${myPython}/include:${myPython}/include/python3.12
          '';
        };
      }
    );
}
