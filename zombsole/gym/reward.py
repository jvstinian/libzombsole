from abc import ABC, abstractmethod


class AgentRewardsInterface(ABC):
    @abstractmethod
    def get_total_reward(self) -> float:
        pass
    
    @abstractmethod
    def get_game_end_reward(self, won: bool) -> float:
        pass


class AgentRewards(AgentRewardsInterface):
    # class AgentState(object):
    #     def __init__(self, agent):
    #         self.alive = (agent.life > 0)
    #         self.life = agent.life

    #     def get_total_reward(self):
    #         return (
    #             self.life
    #         )

    def __init__(self, agents, world, game_end_value, include_life_in_reward=False, include_players_health=False):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0
        # self.players_health = game.get_players_health()
        self.game_end_value = game_end_value
        self.include_life_in_reward = include_life_in_reward
    
    def reset(self, agents, world):
        self.agents_life = [agent.life for agent in agents]
        self.zombie_deaths = 0
        # self.players_health = game.get_players_health()

    def update(self, agents, world):
        prev_reward = self.get_total_reward()
        for idx in range(0, len(self.agents_life)):
            self.agents_life[idx] = agents[idx].life
        self.zombie_deaths = world.zombie_deaths
        # self.players_health = game.get_players_health()
        return self.get_total_reward() - prev_reward

    def get_total_reward(self):
        reward = self.zombie_deaths
        if self.include_life_in_reward:
            reward += sum(self.agents_life)
        # if self.include_players_health:
        #     reward += self.players_health
        return reward

    def get_game_end_reward(self, won: bool):
        if won:
            return self.game_end_value
        else:
            return -1*self.game_end_value
 
