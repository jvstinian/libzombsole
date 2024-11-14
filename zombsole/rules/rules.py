class Rules(object):
    """Rules to decide when a game ends, and when it's won."""
    def __init__(self, game):
        self.game = game

    def players_alive(self):
        """Are there any alive players?"""
        for player in self.game.get_all_players():
            if player.life > 0:
                return True
        return False

    def agents_alive(self):
        """Are there any agents alive?"""
        for player in self.game.agents:
            if player.life > 0:
                return True
        return False

