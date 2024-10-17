# 0.8.2

Adding multi-agent support to interactive zombsole.

# 0.8.1

The single-agent environment `ZombsoleGymEnv` now accepts the actions as dict types directly.  An additional environment `ZombsoleGymEnvDiscreteAction` which accepts the discrete actions has been set up as a wrapper class.

# 0.8.0

Adding a Multi-Agent environment.

# 0.7.0

Fixing and updating actions for agents. The targeted attack has been fixed, the "heal" action now uses the relative coordinates to target the healing, and a "heal_closest" action has been added to heal the closest player.

# 0.6.2

Fixing the encoding of life when using simple encoding.

# 0.6.1

Truncate gym play when agents are no longer alive.

# 0.6.0

Adding support to the Gym environment for producing observations with world or local scope, and 
for encoding positions with simple values or with channels.

# 0.5.4

Building the renderer and providing to the game rather than having the game construct the renderer.
Adding support for specifying the renderer in the interactive JSON mode.

# 0.5.3

Removing initial game config from the interactive json setup. Clients will now need to specify the game configuration before starting a game.

# 0.5.2

Adding zombie deaths to terminal rendering.

# 0.5.1

Using composition rather than inheritance for `ZombsoleGymEnv`.

# 0.5.0

Adding support for running the game using JSON over stdout and stdin. 
This makes it possible to run the game in a subprocess and submit actions 
using other programming languages.

# 0.4.0

Adding support for rendering with `OpenCV` and `PIL` (`pillow`).

# 0.3.1

The version was not updated for a significant period, and so this includes work 
done in the original repo, as well as changes such as refactoring as a library.

