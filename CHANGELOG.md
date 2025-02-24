# 0.11.2

Adding support to the multi-agent environment for using the simple observation style in addition to the channels observation style.

# 0.11.1

Adapting the multi-agent environment to the PettingZoo parallel environment interface.
Adding a wrapper to the multi-agent environment to support discrete actions.

# 0.11.0

Adjusting the reset method in gym implementations to return both an initial observation and an info dictionary.
This is to align with the gym specification.

# 0.10.1

Fixing frame size definition in single-agent gym environment to support each observation style.

# 0.10.0

Registering two gym environments, 
* jvstinian/Zombsole-v0, which uses the world scope, and 
* jvstinian/Zombsole-SurroundingsView-v0, which uses the surroundings scope with a width of 21.

# 0.9.3

Fixing the observation space box size used in the multi-agent environment.

# 0.9.2

Adding functionality for specifying the weapons provided to the agents.
This includes allowing for a weapon to be chosen randomly when the agent is created.

# 0.9.1

Using the rewards class for tracking rewards in the multi-agent environment.

# 0.9.0

Separating the logic for calculating rewards for single agent environments into a separate class.

# 0.8.10

Refactoring rules.

# 0.8.9

Fixing safehouse and evacuation rules to consider agents in addition to legacy players.

# 0.8.8

Coercing observations to use int32 to align with observation space specification.

# 0.8.7

Making sure the players remain in bounds when moving.

# 0.8.6

Fixing action space on discrete action wrapper of gymnasium environment.

# 0.8.5

Fixing the map size determined on map file read.

# 0.8.4

We add a render call to the interactive json application after `step` is called on the gymnasium environment. We previously added the renderer to the class but did not call it.

# 0.8.3

Adding multi-agent support to interactive zombsole.

# 0.8.2

Adding static method to the Map class to allow a user of the package to load a Map using the map name.  To support loading a map outside of python, a method has been added that returns the path to the map file for a given map name.

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

