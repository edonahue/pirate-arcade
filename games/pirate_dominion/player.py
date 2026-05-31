import constants as c

class Player:
    def __init__(self, idx, name, token, is_ai=False, difficulty=None):
        self.idx = idx
        self.name = name
        self.token = token
        self.is_ai = is_ai
        self.difficulty = difficulty or 'medium'
        self.color = c.PD_PLAYER_COLORS[idx]
        self.money = c.PD_STARTING_MONEY
        self.position = 0
        self.properties = []
        self.bankrupt = False
        self.in_jail = False
        self.jail_attempts = 0
        self.skip_turns = 0
        self.jail_free_cards = {'chance': False, 'chest': False}

    @property
    def net_worth(self):
        total = self.money
        for prop_idx in self.properties:
            from constants import PD_PROPERTIES
            total += PD_PROPERTIES[prop_idx][2]
        return total

    def reset(self):
        self.money = c.PD_STARTING_MONEY
        self.position = 0
        self.properties = []
        self.bankrupt = False
        self.in_jail = False
        self.jail_attempts = 0
        self.skip_turns = 0
        self.jail_free_cards = {'chance': False, 'chest': False}
