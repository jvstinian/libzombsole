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
 

# NOTE: The following interface and class was added with the original intent being 
#       to use it for reward tracking in the multi-agent gym setup.
#       At this point we are continuing to use the AgentRewards class for the multi-agent 
#       environment, calculating only a "shared" reward for all agents, rather than 
#       agent-specific rewards.
#       As such we have commented-out the code, and it should be removed if it is 
#       not ultimately used.
#       If we do decide to use this approach, we could even replace the AgentRewards 
#       with a suitable wrapper of MultiAgentRewards.
# from typing import List
# class MultiAgentRewardsInterface(ABC):
#     @abstractmethod
#     def reset(self) -> None:
#         pass
# 
#     # A method for a tuple of the shared and agent-specific rewards
#     @abstractmethod
#     def get_total_rewards(self) -> Tuple[float, List[float]]:
#         pass
#  
#     @abstractmethod
#     def get_game_end_reward(self, won: bool) -> float:
#         pass
# 
# 
# class MultiAgentRewards(MultiAgentRewardsInterface):
#     def __init__(self, agents, world, game_end_value, include_life_in_reward=True):
#         self.agents_life = [agent.life for agent in agents]
#         self.zombie_deaths = 0
#         self.game_end_value = game_end_value
#         self.include_life_in_reward = include_life_in_reward
#     
#     def reset(self, agents, world):
#         self.agents_life = [agent.life for agent in agents]
#         self.zombie_deaths = 0
# 
#     def update(self, agents, world):
#         prev_shared_reward, prev_agent_rewards = self.get_total_rewards()
#         for idx in range(0, len(self.agents_life)):
#             self.agents_life[idx] = agents[idx].life
#         self.zombie_deaths = world.zombie_deaths
#         curr_shared_reward, curr_agent_rewards = self.get_total_rewards()
#         return (
#             curr_shared_reward - prev_shared_reward,
#             list(
#                 map(
#                     lambda vals: vals[1] - vals[0], 
#                     zip(prev_agent_rewards, curr_agent_rewards)
#                 )
#             )
#         )
# 
#     def get_total_rewards(self):
#         shared_reward = self.zombie_deaths
#         agent_rewards = [0.0] ** len(self.agents_life)
#         if self.include_life_in_reward:
#             agent_rewards = list(map(lambda life: life/100.0, self.agents_life))
#         return (shared_reward,  agent_rewards)
# 
#     def get_game_end_reward(self, won: bool):
#         if won:
#             return self.game_end_value
#         else:
#             return -1*self.game_end_value
 
