from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app

from nodes_expand_subtree import leaf_select_drone_random, leaf_action_noop, decorator_extra_hatchery,\
    leaf_build_hatchery, selector_build_extra_hatchery, decorator_step_obs, selector_can_group_hatchery, leaf_select_hatchery, \
    leaf_group_hatchery, holding_BTZSequence, selector_can_select_hatchery
from BeTr_Zerg import BTZSequence, BTZRoot


class ExpandAgent(base_agent.BaseAgent):
    root = BTZRoot([])

    def __init__(self):
        super(ExpandAgent, self).__init__()

        self.gas_harvesters = 0

        self.attack_coordinates = None

    def unit_type_is_selected(self, obs, unit_type):

        if (len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type):
            return True

        if (len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type):
            return True

        return False

    def get_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.feature_units
                if unit.unit_type == unit_type]

    def can_do(self, obs, action):
        return action in obs.observation.available_actions

    def step(self, obs):

        super(ExpandAgent, self).step(obs)

        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative ==
                                  features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()

            self.build_tree()
            self.root.setup(obs)

            self.gas_harvesters = 0

            if xmean <= 31 and ymean <= 31:
                self.root.write("attack_coords", (49, 49))
            else:
                self.root.write("attack_coords", (12, 16))

            self.root.write("hatcheries", {"main" : (xmean,ymean)})

        self.root.execute(obs)
        #   print(self.root.act())
        return self.root.act()

    def build_tree(self):
        nop = leaf_action_noop()

        build_hatchery = leaf_build_hatchery()
        get_hatchery = leaf_select_hatchery()
        group_hatchery = leaf_group_hatchery()
        get_drone = leaf_select_drone_random()

        select_group_extra = selector_can_group_hatchery([group_hatchery, nop])
        select_build_extra = selector_build_extra_hatchery([build_hatchery, nop])
        select_get_extra = selector_can_select_hatchery([get_hatchery, nop])

        trn_extra = holding_BTZSequence([get_drone, select_build_extra, select_get_extra, select_group_extra])

        dec_extra = decorator_extra_hatchery([trn_extra])

        observe = decorator_step_obs([dec_extra])

        self.root = BTZRoot([observe])
