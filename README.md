# Note About This Project

This project is a fork of [fisadev's zombsole](https://github.com/fisadev/zombsole). 
The reason for this fork is to adapt zombsole from a programming game to 
a reinforcement learning environment. 
The author of this repo chose to mirror the original repo 
so as to give credit to the original contributors by preserving 
the commit history. 

We make some other changes as well, including 
* refactoring the code to be a python package that can be installed using `pip`,
* adding some very simple test cases,
* adapting the game play to the Gymnasium API,
* introducing multi-agent play, and
* adding support for rendering with `OpenCV` and `pillow`.

# Installing

To install ``zombsole`` as a python package, the following 
command can be used: 

    pip install git+https://github.com/jvstinian/libzombsole.git

For convenience, an executable script is also installed, which 
can be run using 

    zombsole [ARGUMENTS]

# Nix

Alternatively, nix users can use the flake to build or run `zombsole`.

## Build

To build the `zombsole`, use 
```
nix build github:jvstinian/libzombsole
```
which will install the scripts that can then be run
(from the directory the command was run in) with
```
./result/bin/zombsole extermination me,terminator:2 -m bridge -z 10 -n 0 -b
```

## Run

To skip the build step and run the application, the following can be used:
```
nix run github:jvstinian/libzombsole -- extermination me,terminator:2 -m bridge -z 10 -n 0 -b
```

## Development (Shell)

The flake also provides a development shell, which can be entered using 
```
nix develop github:jvstinian/libzombsole
```

# Zombsole Documentation

The original documentation for the project can be found in this repo at 
[libzombsole/README.rst](./documentation/README.rst)
or in the [original repo](https://github.com/fisadev/zombsole/blob/master/README.rst). 

