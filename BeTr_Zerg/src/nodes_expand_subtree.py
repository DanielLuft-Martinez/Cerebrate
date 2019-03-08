from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random, math
import numpy as np

from BeTr_Zerg import BTZLeaf, BTZSelector, BTZN, BTZDecorator, BTZSequence

""" HELPER FUNCTIONS """
def can_do(self, obs, action):
    return action in obs.observation.available_actions


def get_units_by_type(obs, unit_type):
    return [unit for unit in obs.observation.feature_units
            if unit.unit_type == unit_type]


def transform_relative_to_hatchery(hatchery, x_dist, y_dist):
    if hatchery[0] < 32 and hatchery[1] < 32:  # top left
        return [math.floor(hatchery[0]) + x_dist, math.floor(hatchery[1]) + y_dist]

    elif hatchery[0] < 32 and hatchery[1] >= 32:  # bottom left
        return [math.floor(hatchery[0]) + x_dist, math.floor(hatchery[1]) - y_dist]

    elif hatchery[0] >= 32 and hatchery[1] < 32:  # top right
        return [math.floor(hatchery[0]) - x_dist, math.floor(hatchery[1]) + y_dist]

    else:  # bottom right
        return [math.floor(hatchery[0]) - x_dist, math.floor(hatchery[1])-y_dist]



class leaf_action_noop(BTZLeaf):

    def execute(self):
        BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()

    def __init__(self):
        self.name = self.name + " Action NO-OP"


class holding_BTZSequence(BTZSequence):  # fix name
    def execute(self):
        if self.next_child == 0:
            self.setup()
        if self.next_child in range(0, len(self.children) - 1):
            list(map(lambda x: x.execute(), [self.children[self.next_child]]))
            if not BTZN().blackboard["action"] == actions.FUNCTIONS.no_op():
                self.next_child += 1
        else:
            BTZN().blackboard["current_sequence"] = self.previous_sequence
            list(map(lambda x: x.execute(), [self.children[self.next_child]]))
            self.next_child = 0


""" DECORATOR FUNCTIONS"""
class decorator_step_obs(BTZDecorator):

    def execute(self):
        BTZDecorator.execute(self)

    def __init__(self, decendant):
        self.children = decendant
        BTZN().blackboard["free_supply"] = 0
        BTZN().blackboard["spawning_pools"] = 0

        BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
        self.name = self.name + " Obs"


""" BUILD EXTRA BASE SEQUENCE """
class decorator_extra_hatchery(BTZDecorator):
    def execute(self):
        BTZN().blackboard["new_hatchery_X"], BTZN().blackboard["new_hatchery_Y"] = transform_relative_to_hatchery(BTZN().blackboard["hatcheries"]["main"], 30, 30)
        BTZN().blackboard["hatchery_group"] = 6
        BTZN().blackboard["new_hatchery"] = "extra"

        BTZDecorator.execute(self)

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " extra_hatchery"


class leaf_select_drone_random(BTZLeaf):
    def execute(self):  # assume has drones
        drone = random.choice(get_units_by_type((BTZN().blackboard["obs"]), units.Zerg.Drone))
        BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (drone.x, drone.y))

    def __init__(self):
        self.name = self.name + " Random Drone Select"


class selector_build_extra_hatchery(BTZSelector):
    def decide(self):
        """
        minimap = self.blackboard['obs'].observation.feature_minimap.player_relative
        minerals = []
        me = []
        for i in range(len(minimap)):
            minerals.append([x if x == 3 else 0 for x in minimap[i]])
            me.append([x if x == 1 else 0 for x in minimap[i]])
        minerals = np.nonzero(minerals)
        me = np.mean(np.nonzero(me), axis=1)
       """
        if can_do(self, (BTZN().blackboard["obs"]), actions.FUNCTIONS.Build_Hatchery_screen.id) and "extra" not in BTZN().blackboard["hatcheries"]:
            self.decision = 0  # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1  # cant, so NOOP

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Extra Hatchery?"


class leaf_build_hatchery(BTZLeaf):
    def execute(self):  # assume larva selected
        x = BTZN().blackboard["new_hatchery_X"]
        y = BTZN().blackboard["new_hatchery_Y"]
        BTZN().blackboard["hatcheries"]["extra"] = (x, y)
        BTZN().blackboard["action"] = actions.FUNCTIONS.Build_Hatchery_screen("now", (x, y))


    def __init__(self):
        self.name = self.name + "  Build Hatchery"


class selector_can_select_hatchery(BTZSelector):

    def check_range(self, no, range, list_nos):
        for number in list_nos:
            if (no - range <= number) and (no + range >= number):
                return True


    def decide(self):
        x, y = BTZN().blackboard["hatcheries"][BTZN().blackboard["new_hatchery"]]
        hatcheries = get_units_by_type(BTZN().blackboard["obs"], 86)
        hatches_x = [hatch.x for hatch in hatcheries]
        hatches_y = [hatch.y for hatch in hatcheries]
        if self.check_range(x, 5, hatches_x) and self.check_range(y, 5, hatches_y):
            self.decision = 0  # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1  # cant, so NOOP

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Select Extra Hatchery?"


class selector_can_group_hatchery(BTZSelector):
    def decide(self):
       if BTZN().blackboard["obs"].observation.single_select[0][0] == 86:
            self.decision = 0  # it is a possible action - 0 is procede with building it
       else:
            self.decision = 1  # cant, so NOOP

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Group Extra Hatchery?"


class leaf_select_hatchery(BTZLeaf):
    def execute(self):  # assume larva selected
        x, y = BTZN().blackboard["hatcheries"][BTZN().blackboard["new_hatchery"]]
        BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (x, y))

    def __init__(self):
        self.name = self.name + " select hatchery"


class leaf_group_hatchery(BTZLeaf):
    def execute(self):  # assume larva selected
        BTZN().blackboard["action"] = actions.FUNCTIONS.select_control_group("set", BTZN().blackboard["hatchery_group"])

    def __init__(self):
        self.name = self.name + "  Set extra hatchery to control group 6"


""" BUILD NATURAL BASE SEQUENCE"""
# sequence: dec -> select drone -> move camera -> build hatchery -> move camera back to base

class decorator_natural_hatchery(BTZDecorator):
    def execute(self):
        BTZN().blackboard["new_hatchery_X"] = 256
        BTZN().blackboard["new_hatchery_Y"] = 256

        BTZDecorator.execute(self)

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " natural_hatchery"


class leaf_move_camera_to_natural(BTZLeaf):
    def execute(self):  # assume larva selected
        x = BTZN().blackboard["new_hatchery_X"]
        y = BTZN().blackboard["new_hatchery_Y"]
        BTZN().blackboard["action"] = actions.FUNCTIONS.Build_Hatchery_screen("now", x, y)
        BTZN().blackboard["hatcheries"]["extra"] = (x, y)

    def __init__(self):
        self.name = self.name + "  Move camera to natural"


""" REBUILD """
# sequence: get damaged buildings -> select drone(s) -> repair buildings with drone(s)
class decorator_rebuild_buildings(BTZDecorator):

    def execute(self):
        my_building_locations = []
        for building in self.building_list:
            my_building_locations.append(get_units_by_type(BTZN().blackboard["obs"], building))


        BTZDecorator.execute(self)

    def __init__(self, decendant):
        self.building_list = { "BanelingNest":96, "Hatchery":86, "Hive":101, "Extractor":88, "Lair":100, "CreepTumor":87, "GreaterSpire":102, "CreepTumorBurrowed":137, "CreepTumorQueen":138, "EvolutionChamber":90, "HydraliskDen":91, "InfestationPit":94, "LurkerDen":504, "NydusCanal":142, "NydusNetwork":95, "SpawningPool":89, "SpineCrawler":98, "SpineCrawlerUprooted":139, "Spire":92, "SporeCrawler":99, "SporeCrawlerUprooted":140, "UltraliskCavern":93}

        self.children = decendant
        self.name = self.name + " rebuild_buildings"


