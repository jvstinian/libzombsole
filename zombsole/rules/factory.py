from zombsole.rules.extermination import ExterminationRules
from zombsole.rules.survival import SurvivalRules
from zombsole.rules.evacuation import EvacuationRules
from zombsole.rules.safehouse import SafeHouseRules


class RulesFactory(object):
    @staticmethod
    def create_rules(rules_name, game):
        if rules_name == "extermination":
            return ExterminationRules(game)
        elif rules_name == "survival":
            return SurvivalRules(game)
        elif rules_name == "evacuation":
            return EvacuationRules(game)
        elif rules_name == "safehouse":
            return SafeHouseRules(game)
        else:
            raise ValueError(f"{rules_name} is not a valid rule name.  Valid options are extermination, survival, evacuation, and safehouse")

