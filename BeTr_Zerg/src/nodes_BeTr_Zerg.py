'''
Created on Feb 11, 2019

@author: Daniel
'''
from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random

from BeTr_Zerg import BTZLeaf, BTZSelector, BTZN, BTZDecorator

""" HELPER FUNCTIONS """

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

""" MISC NODES """

class decorator_step_obs(BTZDecorator):
    
    
    def execute(self):
        BTZN().blackboard["free_supply"] = (BTZN().blackboard["obs"].observation.player.food_cap -
                                             BTZN().blackboard["obs"].observation.player.food_used)
        BTZDecorator.execute(self)
    
    def __init__(self, decendant):
        self.children = decendant
        BTZN().blackboard["free_supply"] = 0
        BTZN().blackboard["spawning_pools"] = 0
        
        BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
        self.name = self.name + " Obs"
        
        
class leaf_action_noop(BTZLeaf):
    
    def execute(self):
        BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
    
    def __init__(self):
        
        self.name = self.name + " Action NO-OP"
    
class leaf_attack(BTZLeaf):
    
    def execute(self):
        BTZN().blackboard["action"] = actions.FUNCTIONS.Attack_minimap("now", BTZN().blackboard["attack_coords"])
        
    def __init__(self):
        self.name = self.name + " Attack"
        
class leaf_select_army(BTZLeaf):
    
    def execute(self):
        BTZN().blackboard["action"] = actions.FUNCTIONS.select_army("select")
        
    def __init__(self):
        self.name = self.name + " Select Army"
    
    
""" SPAWNING POOL SEQUENCE """

class selector_spawning_pool_exist(BTZSelector):
    
    def decide(self):
        
        if len(get_units_by_type(self, BTZN().blackboard["obs"], units.Zerg.SpawningPool)) == 0:
            self.decision = 0 #does not have sp - 0 is build sp sequence
            self.spawning_pools = [1]
        else:
            self.decision = 1 #does have - 1 is other actions
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Spawning Pool?"
        

class leaf_select_drone_random(BTZLeaf):
    
    def execute(self): #assume has drones
        drone = random.choice(get_units_by_type(self, (BTZN().blackboard["obs"]), units.Zerg.Drone))
        BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (drone.x,drone.y))

    
    def __init__(self):
        self.name = self.name + " Random Drone Select"
        
        
class selector_can_build_spawning_pool(BTZSelector):
    
    def decide(self):
        if can_do(self, (BTZN().blackboard["obs"]), actions.FUNCTIONS.Build_SpawningPool_screen.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Spawning Pool?"
        
           
class leaf_build_spawning_pool(BTZLeaf):
    
    def execute(self):
        gasY,gasX = (((BTZN().blackboard["obs"]).observation.feature_screen.unit_type == 343 ).nonzero())
        x = random.choice(gasX)
        y = random.choice(gasY)
        BTZN().blackboard["action"] = actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))
    
    def __init__(self):
        self.name = self.name + " Build Spawning Pool" 
        
        
""" MAKE 'UNIT' SEQUENCE """

class selector_select_unit(BTZSelector):
    
    unit_type = 0
    def decide(self):
        if unit_type_is_selected(self, BTZN().blackboard["obs"], self.unit_type):
            self.decision = 0 # unit is selected, proceed
        else:
            self.decision = 1 # not selected, so do something else
    
    def __init__(self, decendant, unit_type):
        self.children = decendant
        self.unit_type = unit_type
        self.name = self.name + " Unit ?"
        
class leaf_select_unit_random(BTZLeaf):
    
    unit_type = 0
    def execute(self): #assume has drones
        units = get_units_by_type(self, (BTZN().blackboard["obs"]), self.unit_type)
        if len(units) > 0 and (type(units) != None):
            unit = random.choice(units)
            BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (unit.x,unit.y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()

    
    def __init__(self, unit_type):
        self.name = self.name + " Random UNIT Select"
        self.unit_type = unit_type
        
class leaf_select_unit_all(BTZLeaf):
    
    unit_type = 0
    def execute(self): #assume has drones
        units = get_units_by_type(self, (BTZN().blackboard["obs"]), self.unit_type)
        if len(units) > 0 and (type(units) != None):
            unit = random.choice(units)
            BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select_all_type", (unit.x,unit.y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
    
    def __init__(self, unit_type):
        self.name = self.name + " All UNIT Type Select"
        self.unit_type = unit_type
        
class leaf_train_overlord(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, BTZN().blackboard["obs"], actions.FUNCTIONS.Train_Overlord_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Overlord_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Overlord"

class leaf_train_drone(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, BTZN().blackboard["obs"], actions.FUNCTIONS.Train_Drone_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Drone_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Drone"

class leaf_train_zergling(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, BTZN().blackboard["obs"], actions.FUNCTIONS.Train_Zergling_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Zergling_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Zergling"

class leaf_train_queen(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, BTZN().blackboard["obs"], actions.FUNCTIONS.Train_Queen_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Queen_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Queen"
        
class selector_queen_upkeep(BTZSelector):
    
    def decide(self):
        if (BTZN().blackboard["time"]%45 == 1):
            self.decision = 0
        else:
            self.decision = 1
                
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Queen Upkeep"  
        
class leaf_queen_inject_larva(BTZLeaf):     
    
    def execute(self):
        if can_do(self, BTZN().blackboard["obs"], actions.FUNCTIONS.Effect_InjectLarva_screen.id):
            hatch = random.choice(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Hatchery))
            BTZN().blackboard["action"] = actions.FUNCTIONS.Effect_InjectLarva_screen("now",(hatch.x,hatch.y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()

    def __init__(self):
        self.name = self.name + " Inject Larva"
        
class selector_build_phase(BTZSelector):
    
    def decide(self):
        self.decision = BTZN().blackboard["Phase"]
        
            
    def __init__(self, decendants):
        self.children = decendants
        BTZN().blackboard["Phase"] = 0
        self.name = self.name + " Build Phase"
        
class decorator_phase(BTZDecorator):
    
    def execute(self):
        if ((len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Queen)) > 0) 
            and( len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Zergling)) <10)):
            BTZN().blackboard["Phase"] = 1 #prep
            #print("phase 1")
        elif len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Zergling)) >10:
            BTZN().blackboard["Phase"] = 2 #attack
            #print("phase 2")
            
        BTZDecorator.execute(self)
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Phase"
        
        
class selector_ling_attack_wave(BTZSelector):
    
    def decide(self):       
        if len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Zergling)) < 10:
            self.decision = 0 # not enough lings train more
            #print(len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Zergling)))
        else:
            self.decision = 1 # send wave
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Wave Attack"


class selector_supply(BTZSelector):
    
    unit_type = 0
    def decide(self):
        if BTZN().blackboard["free_supply"] == 0:
            self.decision = 0 # no supply, build overlord
        else:
            self.decision = 1 # carry on
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Free Supply"
        
        
        
        
