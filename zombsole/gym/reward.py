from typing import List
from abc import ABC, abstractmethod


class AgentRewardsInterface(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass
    
    @abstractmethod
    def get_total_reward(self) -> float:
        pass
    
    @abstractmethod
    def get_game_end_reward(self, won: bool) -> float:
        pass


class AgentRewards(AgentRewardsInterface):
    def __init__(self, agents, world, game_end_value, include_life_in_reward=True):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0
        self.game_end_value = game_end_value
        self.include_life_in_reward = include_life_in_reward
    
    def reset(self, agents, world):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0

    def update(self, agents, world):
        prev_reward = self.get_total_reward()
        for idx in range(0, len(self.agents_life)):
            self.agents_life[idx] = agents[idx].life
        self.zombie_deaths = world.zombie_deaths
        return self.get_total_reward() - prev_reward

    def get_total_reward(self):
        reward = self.zombie_deaths
        if self.include_life_in_reward:
            reward += sum(self.agents_life)/100.0
        return reward

    def get_game_end_reward(self, won: bool):
        if won:
            return self.game_end_value
        else:
            return -1*self.game_end_value
 

# If we do decide to continue with this approach, we could even replace the AgentRewards 
# with a suitable wrapper of MultiAgentRewards.
class MultiAgentRewardsInterface(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass

    # A method for agent-specific rewards
    @abstractmethod
    def get_total_rewards(self) -> List[float]:
        pass
 
    @abstractmethod
    def get_game_end_reward(self, won: bool) -> float:
        pass


class MultiAgentRewards(MultiAgentRewardsInterface):
    def __init__(self, agents, world, game_end_value): # , include_life_in_reward=True):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0
        self.game_end_value = game_end_value
        # self.include_life_in_reward = include_life_in_reward
    
    def reset(self, agents, world):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0

    def update(self, agents, world):
        prev_agent_rewards = self.get_total_rewards()
        for idx in range(0, len(self.agents_life)):
            self.agents_life[idx] = agents[idx].life
        self.zombie_deaths = world.zombie_deaths
        curr_agent_rewards = self.get_total_rewards()
        return list(
            map(
                lambda vals: vals[1] - vals[0], 
                zip(prev_agent_rewards, curr_agent_rewards)
            )
        )

    def get_total_rewards(self):
        agent_rewards = list(map(lambda life: self.zombie_deaths + life/100.0, self.agents_life))
        return agent_rewards

    def get_game_end_reward(self, won: bool):
        if won:
            return self.game_end_value
        else:
            return -1*self.game_end_value
 
