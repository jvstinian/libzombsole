import json
from typing import Dict, Union
from abc import ABC, abstractmethod
from json import JSONEncoder
from zombsole.gym_env import ZombsoleGymEnv


class GameResponse(ABC):
    def to_dict(self) -> Dict:
        return {
            "tag": self.get_tag(),
            "parameters": self.get_parameters()
        }

    @abstractmethod
    def get_tag(self) -> str:
        pass

    @abstractmethod
    def get_parameters(self) -> Dict:
        pass

class GameStateEncoder(JSONEncoder):
    def default(self, o: GameResponse):
        try:
            d = o.to_dict()
        except TypeError:
            pass
        else:
            return d
        # Let the base class default method raise the TypeError
        return super().default(o)

class GameStateResponse(GameResponse):
    def __init__(self, status: str, active: bool, config_required: bool, last_observation: Union[None, Dict] = None):
        self.status = status
        self.active = active
        self.config_required = config_required
        self.last_observation = last_observation

    def get_tag(self) -> str:
        return "GameState"
    
    def get_parameters(self) -> Dict:
        return {
            "status": self.status,
            "active": self.active,
            "config_required": self.config_required,
            "last_observation": self.last_observation
        }

class GameObservationResponse(GameResponse):
    def __init__(self, last_observation: Dict = None):
        self.last_observation = last_observation

    def get_tag(self) -> str:
        return "GameObservation"
    
    def get_parameters(self) -> Dict:
        return self.last_observation

class ErrorResponse(GameResponse):
    def __init__(self, message: str):
        self.message = message

    def get_tag(self) -> str:
        return "Error"
    
    def get_parameters(self) -> Dict:
        return self.message

class GameConfig(object):
    def __init__(self, rules_name: str, map_name: str, players, agent_ids, initial_zombies=10, minimum_zombies=10):
        self.rules_name = rules_name
        self.map_name = map_name
        self.players = players
        self.agent_ids = agent_ids
        self.initial_zombies = initial_zombies
        self.minimum_zombies = minimum_zombies

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

class GameManagementInterface(ABC):
    @abstractmethod
    def set_game_config(self, game_config: GameConfig):
        pass
    
    @abstractmethod
    def get_game_status(self):
        pass
    
    @abstractmethod
    def start_game(self):
        pass
    
    @abstractmethod
    def step_with_agent_action(self, action: Dict):
        pass

    @abstractmethod
    def exit(self):
        pass

class GameRequest(ABC):
    @staticmethod
    def decode_hook(jsonobj):
        if "tag" in jsonobj:
            if (jsonobj["tag"] in ["GameConfigUpdate", "GameAction"]) and ("parameters" not in jsonobj):
                raise ValueError(f"A GameRequest with tag {jsonobj['tag']} must have key \"parameters\"")
            if jsonobj["tag"] == "GameConfigUpdate":
                return GameConfigUpdateRequest.from_dict(jsonobj["parameters"])
            elif jsonobj["tag"] == "GameStatus":
                return GameStatusRequest()
            elif jsonobj["tag"] == "Exit":
                return ExitRequest()
            elif jsonobj["tag"] == "StartGame":
                return StartGameRequest()
            elif jsonobj["tag"] == "GameAction":
                return GameActionRequest(jsonobj["parameters"])
            else:
                raise ValueError("GameRequest \"tag\" must be \"GameConfigUpdate\", \"GameAction\", \"GameStatus\", \"StartGame\", or \"Exit\"")
        else: # Simply pass the object through (used where objects are passed as parameters)
            return jsonobj

    @abstractmethod
    def update_game_manager(self):
        pass

class GameConfigUpdateRequest(GameRequest):
    def __init__(self, game_config: GameConfig):
        self.game_config = game_config

    @classmethod
    def from_dict(cls, game_config_obj: Dict):
        game_config = GameConfig.from_dict(game_config_obj)
        return cls(game_config)
    
    def update_game_manager(self, game_manager: GameManagementInterface):
        game_manager.set_game_config(self.game_config)

class GameStatusRequest(GameRequest):
    def __init__(self):
        pass
    
    def update_game_manager(self, game_manager: GameManagementInterface):
        game_manager.get_game_status()

class ExitRequest(object):
    def __init__(self):
        pass
    
    def update_game_manager(self, game_manager: GameManagementInterface):
        game_manager.exit()

class StartGameRequest(object):
    def __init__(self):
        pass

    def update_game_manager(self, game_manager: GameManagementInterface):
        game_manager.start_game()

class GameActionRequest(object):
    def __init__(self, action: Dict):
        self.action = action

    def update_game_manager(self, game_manager: GameManagementInterface):
        game_manager.step_with_agent_action(self.action)

class GymEnvManager(GameManagementInterface):
    def __init__(self):
        self.game_config = None
        self.gym_env = None
        self.keep_going = True
        self.last_observation = None
        self.response_encoder = GameStateEncoder(indent=None)

    def _initialize_gym(self):
        if self.game_config is not None:
            self.gym_env = ZombsoleGymEnv(
                self.game_config.rules_name, 
                self.game_config.players,
                self.game_config.map_name,
                self.game_config.agent_ids,
                initial_zombies=self.game_config.initial_zombies, 
                minimum_zombies=self.game_config.minimum_zombies, 
                debug=False
            )
            self.last_observation = None
    
    def _env_status(self):
        if not self.keep_going:
            return "exiting"
        elif self.last_observation is None:
            return "wating for game"
        else:
            "game in progress"

    def _get_game_state(self):
        status = self._env_status()
        config_required = self.game_config is None

        return GameStateResponse(status, self.keep_going, config_required, self.last_observation)

    def _resposne_to_stdout(self, response):
        print(self.response_encoder.encode(response.to_dict()))

    def run(self):
        self._resposne_to_stdout(self._get_game_state())
        while self.keep_going:
            message = input()
            try: 
                obj = json.loads(message, object_hook=GameRequest.decode_hook)
            except Exception as ex:
                err = ErrorResponse(str(ex))
                self._resposne_to_stdout(err)
            else:
                obj.update_game_manager(self)
    
    # Implementing the interface
    def set_game_config(self, game_config: GameConfig):
        self.game_config = game_config
        self._initialize_gym()
        self._resposne_to_stdout(
            self._get_game_state()
        )

    def get_game_status(self):
        self._resposne_to_stdout(
            self._get_game_state()
        )
    
    def start_game(self):
        observation = self.gym_env.reset().tolist()
        self.last_observation = {
            "observation": observation,
            "reward": 0,
            "done": False,
            "truncated": False,
            "info": None
        }
        self._resposne_to_stdout(
            GameObservationResponse(
                self.last_observation
            )
        )
    
    def step_with_agent_action(self, action: Dict):
        action_id = ZombsoleGymEnv.game_actions.index(action)
        observation, reward, done, truncated, info = self.gym_env.step(action_id)
        self.last_observation = {
            "observation": observation.tolist(),
            "reward": reward,
            "done": done,
            "truncated": truncated,
            "info": info
        }
        self._resposne_to_stdout(
            GameObservationResponse(
                self.last_observation
            )
        )

    def exit(self):
        self.keep_going = False
        self._resposne_to_stdout(
            self._get_game_state()
        )

def play_interactive_json():
    """Initiate a game, using the command line arguments as configuration."""
    game_manager = GymEnvManager()
    game_manager.run()

if __name__ == '__main__':
    play_interactive_json()

