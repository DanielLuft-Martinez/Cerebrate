'''
Created on Feb 11, 2019

@author: Daniel
'''
from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random

from BeTr_Zerg import *


""" HELPER FUNCTIONS """

def unit_type_is_selected(self, unit_type):
    obs =  BTZN().blackboard["obs"]
    if (len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type):
        return True
    
    if (len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type):
        return True
    
    return False

def _get_units_by_type(self,  unit_type):#use ONLY for htac,lair,hive check
    obs =  BTZN().blackboard["obs"]
        
    return [unit for unit in obs.observation.feature_units
            if unit.unit_type == unit_type]


def get_units_by_type(self,  unit_type):
    obs =  BTZN().blackboard["obs"]
    if unit_type == units.Zerg.Hatchery:
        if (len(_get_units_by_type(self, units.Zerg.Lair)) > 0):
            unit_type = units.Zerg.Lair
        elif (len(_get_units_by_type(self, units.Zerg.Hive)) > 0):
            unit_type = units.Zerg.Hive
        
    return [unit for unit in obs.observation.feature_units
            if unit.unit_type == unit_type]


def can_do(self, action):
    obs =  BTZN().blackboard["obs"]
    return action in obs.observation.available_actions

def transformDistance(self, x, x_distance, y, y_distance):
        if not BTZN().blackboard["base_top_left"]:
            return [x - x_distance, y - y_distance]

        return [x + x_distance, y + y_distance]

def transformLocation(self, x, y):
        if not BTZN().blackboard["base_top_left"]:
            return [64 - x, 64 - y]

        return [x, y]
def tech_check(self, unit_type, name):
    if(len(get_units_by_type(self,unit_type))>0):
        unit = random.choice(get_units_by_type(self, unit_type))
        BTZN().blackboard["tech_buildings"][name] = [unit.x, unit.y]
        
    
""" MISC NODES """

class decorator_step_obs(BTZDecorator):
    
    
    def execute(self):
        BTZN().blackboard["free_supply"] = (BTZN().blackboard["obs"].observation.player.food_cap -
                                             BTZN().blackboard["obs"].observation.player.food_used)
        ##tech obs
        tech_check(self, units.Zerg.SpawningPool, "spawning_pool")
        tech_check(self, units.Zerg.RoachWarren, "roach_warren")
        tech_check(self, units.Zerg.Lair, "lair")
        tech_check(self, units.Zerg.EvolutionChamber, "evolution_chamber")
        tech_check(self, units.Zerg.Spire, "spire")
        tech_check(self, units.Zerg.HydraliskDen, "hydralisk_den")
        
        
        
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
        if  can_do(self,  actions.FUNCTIONS.Attack_minimap.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Attack_minimap("now", (BTZN().blackboard["attack_coords"][0] + random.randint(-5,6),BTZN().blackboard["attack_coords"][1] + random.randint(-5,6)))
        
    def __init__(self):
        self.name = self.name + " Attack"
        
class leaf_select_army(BTZLeaf):
    
    def execute(self):
        if  can_do(self,  actions.FUNCTIONS.select_army.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.select_army("select")
        
    def __init__(self):
        self.name = self.name + " Select Army"
        
class leaf_simple_waypoint_close(BTZLeaf):
    
    def execute(self):
       # print("set waypoint: ")
        #hatchery_y, hatchery_x = ( BTZN().blackboard["obs"].observation['feature_screen'][features.SCREEN_FEATURES.unit_type.index] == units.Zerg.Hatchery).nonzero()
        if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
            hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
            if  can_do(self,  actions.FUNCTIONS.Rally_Units_screen.id):
                target = transformDistance(self, round(hatch.x), 15, round(hatch.y), -9)
               # print("set waypoint: ", end = "")
               # print(target)
                BTZN().blackboard["action"] =  actions.FUNCTIONS.Rally_Units_screen("now", target)
            
    def __init__(self):
        self.name = self.name + " Simple Waypoint"
    
""" SPAWNING POOL SEQUENCE """

class selector_spawning_pool_exist(BTZSelector):
    
    def decide(self):
        
        if len(get_units_by_type(self, units.Zerg.SpawningPool)) == 0:
            self.decision = 0 #does not have sp - 0 is build sp sequence
        else:
            self.decision = 1 #does have - 1 is other actions
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Spawning Pool?"
        

class leaf_select_drone_random(BTZLeaf):
    
    def execute(self): #assume has drones
        if len(get_units_by_type(self, units.Zerg.Drone)) > 0:
            drone = random.choice(get_units_by_type(self, units.Zerg.Drone))
            if drone.x >= 0 and drone.y >=0 and drone.x <= 84 and drone.y <= 84 :
                BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (drone.x,drone.y))

    
    def __init__(self):
        self.name = self.name + " Random Drone Select"
        
        
class selector_can_build_spawning_pool(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Build_SpawningPool_screen.id):
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
        
""" build tech """

class selector_can_build_evolution_chamber(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Build_EvolutionChamber_screen.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Evolution Chamber?"
        
class leaf_build_evolution_chamber(BTZLeaf):
    
    def execute(self):
        if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
            hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
            target = transformDistance(self, round(hatch.x), random.randint(-25,11), round(hatch.y), random.randint(-25,11))
            BTZN().blackboard["action"] = actions.FUNCTIONS.Build_EvolutionChamber_screen("now", target)
            
    def __init__(self):
        self.name = self.name + " Build Evolution Chamber" 
        
class selector_can_build_spire(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Build_Spire_screen.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Spire?"
        
class leaf_build_spire(BTZLeaf):
    
    def execute(self):
        if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
            hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
            target = transformDistance(self, round(hatch.x), random.randint(-25,11), round(hatch.y), random.randint(-25,11))
            BTZN().blackboard["action"] = actions.FUNCTIONS.Build_Spire_screen("now", target)
            
    def __init__(self):
        self.name = self.name + " Build Spire" 

class selector_can_build_hydralisk_den(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Build_HydraliskDen_screen.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Hydralisk Den?"
        
class leaf_build_hydralisk_den(BTZLeaf):
    
    def execute(self):
        if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
            hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
            target = transformDistance(self, round(hatch.x), -25, round(hatch.y), random.randint(-25,0))
            BTZN().blackboard["action"] = actions.FUNCTIONS.Build_HydraliskDen_screen("now", target)
            
    def __init__(self):
        self.name = self.name + " Build Hydralisk Den" 

class selector_can_morph_lair(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Morph_Lair_quick.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Morph Lair"
        
           
class leaf_morph_lair(BTZLeaf):
    
    def execute(self):
        
        BTZN().blackboard["action"] = actions.FUNCTIONS.Morph_Lair_quick("now")
        BTZN().blackboard["upgrades"]["lair"] = 1
    
    def __init__(self):
        self.name = self.name + " Morph Lair"


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
        units = get_units_by_type(self, self.unit_type)
        if len(units) > 0 and (type(units) != None):
            unit = random.choice(units)
            if unit.x >= 0 and unit.y >=0 and unit.x <= 84 and unit.y <= 84:
                BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select", (unit.x,unit.y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()

    
    def __init__(self, unit_type):
        self.name = self.name + " Random UNIT Select"
        self.unit_type = unit_type
        
class leaf_select_unit_all(BTZLeaf):
    
    unit_type = 0
    def execute(self): #assume has drones
        units = get_units_by_type(self, self.unit_type)
        if len(units) > 0 and (type(units) != None):
            unit = random.choice(units)
            if unit.x >= 0 and unit.y >=0 and unit.x <= 84 and unit.y <= 84:
                BTZN().blackboard["action"] = actions.FUNCTIONS.select_point("select_all_type", (unit.x,unit.y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
    
    def __init__(self, unit_type):
        self.name = self.name + " All UNIT Type Select"
        self.unit_type = unit_type
        
class leaf_train_overlord(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Overlord_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Overlord_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Overlord"

class leaf_train_drone(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Drone_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Drone_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Drone"

class leaf_train_zergling(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Zergling_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Zergling_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Zergling"
    
class leaf_train_mutalisk(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Mutalisk_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Mutalisk_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Mutalisk"
        
class leaf_train_hydralisk(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Hydralisk_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Hydralisk_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Hydralisk"
        
class leaf_train_corruptor(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Corruptor_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Corruptor_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Corruptor"

class leaf_train_queen(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Queen_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Queen_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Queen"
        
""" Queen Stuff """
        
class selector_queen_upkeep(BTZSelector):
    
    def decide(self):
        if (BTZN().blackboard["time"]%45 == 1):
            self.decision = 0
        else:
            self.decision = 1
                
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Queen Upkeep"  
        
class selector_has_queen_upkeep(BTZSelector):
    
    def decide(self):
        if (len(get_units_by_type(self, units.Zerg.Queen))> 0):
            self.decision = 0 # carry on
        else:
            self.decision = 1 #make queen
                
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Has Queen Upkeep?"  
        
class leaf_queen_inject_larva(BTZLeaf):     
    
    def execute(self):
        if can_do(self, actions.FUNCTIONS.Effect_InjectLarva_screen.id):
            if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
                hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
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
        
class decorator_phase_queen_ling(BTZDecorator):
    
    def execute(self):
        if ((len(get_units_by_type(self, units.Zerg.Queen)) > 0) 
            and( len(get_units_by_type(self, units.Zerg.Zergling)) <10)):
            BTZN().blackboard["Phase"] = 1 #prep
            #print("phase 1")
        elif len(get_units_by_type(self, units.Zerg.Zergling)) >10:
            BTZN().blackboard["Phase"] = 2 #attack
            #print("phase 2")
            
        BTZDecorator.execute(self)
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Phase"
        
        
class selector_ling_attack_wave(BTZSelector):
    
    def decide(self):       
        if len(get_units_by_type(self, units.Zerg.Zergling)) < 10:
            self.decision = 0 # not enough lings train more
            #print(len(get_units_by_type(self,BTZN().blackboard["obs"], units.Zerg.Zergling)))
        else:
            self.decision = 1 # send wave
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Wave Attack"
        
        
        
        
class selector_shift_overlord_cloud(BTZSelector):
        
    def decide(self):
        if unit_type_is_selected(self , units.Zerg.Overlord):
            self.decision = 0
        else:
            self.decision = 1
        
        
        
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Shift Overlord Cloud"
        
class leaf_shift_overlord_cloud(BTZLeaf):
    
    def execute(self):
        ##hatchery_y, hatchery_x = ( BTZN().blackboard["obs"].observation['feature_screen'][features.SCREEN_FEATURES.unit_type.index] == units.Zerg.Hatchery).nonzero()
        if(len(get_units_by_type(self, units.Zerg.Hatchery))>0):
            hatch = random.choice(get_units_by_type(self, units.Zerg.Hatchery))
            if len(get_units_by_type(self, units.Zerg.Overlord)) % 2 == 0:
                target = transformDistance(self, round(hatch.x), -35, round(hatch.y), 0)
            else:
                target = transformDistance(self, round(hatch.x), -25, round(hatch.y), -25)
            if(can_do(self, actions.FUNCTIONS.Move_screen.id)):
                BTZN().blackboard["action"] = actions.FUNCTIONS.Move_screen("now", target)
   #     else:
   #         BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
        
        
    def __init__(self):
        self.name = self.name + " Shift Overlord Cloud"
 

class selector_opening(BTZSelector):
    
    def decide(self):
        self.decsion = BTZN().blackboard["opening"]
        if BTZN().blackboard["opening"] == 1:
            #print("ROACH OPEN")
            self.decision = 1
        else:
            #print("LING OPEN")
            self.decision = 0
        # 0 -> LINGS
        # 1 -> ROACH
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Opening"






class selector_supply(BTZSelector):
    
    unit_type = 0
    def decide(self):
        if BTZN().blackboard["free_supply"] <= 2:
            self.decision = 0 # no supply, build overlord
        else:
            self.decision = 1 # carry on
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Free Supply"
        
"""   Ling Opening SEQUENCE    """

class selector_zergling_opening_phase(BTZSelector):
    done = False
    def decide(self):#build
       # print("Zergling Open") ## nop and 
        if self.done :
            self.decision = 2 # DONE
            #print("Zergling Open Done") ## nop and 
        elif (len(get_units_by_type(self, units.Zerg.SpawningPool)) >= 1  
            and len(get_units_by_type(self, units.Zerg.Extractor)) > 1 
            and len(get_units_by_type(self, units.Zerg.Queen)) >= 1 
            and not self.done ):
            self.decision = 1 #prep
            #print("PREP")
            #print("PREP")
            if len(get_units_by_type(self, units.Zerg.Zergling)) > 10:
                self.done =True
        #else:
            #print("build up")
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Zergling Opening Phase"

     
        
""" Roach Warren opening SEQUENCE """

        
        
class selector_roach_opening_phase(BTZSelector):
    done = False
    def decide(self):#build
       # print("Zergling Open") ## nop and 
        if self.done :
            self.decision = 2 # DONE
            #print("Zergling Open Done") ## nop and 
        elif (len(get_units_by_type(self, units.Zerg.RoachWarren)) >= 1  
            and len(get_units_by_type(self, units.Zerg.Extractor)) > 1 
            and len(get_units_by_type(self, units.Zerg.Queen)) >= 1 
            and not self.done ):
            self.decision = 1 #prep
            #print("PREP")
            #print("PREP")
            if len(get_units_by_type(self, units.Zerg.Roach)) > 5:
                self.done =True
        #else:
            #print("build up")
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Roach Opening Phase"

class selector_roach_warren_exist(BTZSelector):
    
    def decide(self):
        
        if len(get_units_by_type(self, units.Zerg.RoachWarren)) <= 0:
            self.decision = 0 #does not have sp - 0 is build sp sequence
        else:
            self.decision = 1 #does have - 1 is other actions
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Roach Warren?"
        

        
class selector_can_build_roach_warren(BTZSelector):
    
    def decide(self):
        if can_do(self,  actions.FUNCTIONS.Build_RoachWarren_screen.id):
            self.decision = 0 # it is a possible action - 0 is procede with building it
        else:
            self.decision = 1 # cant, so NOOP
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Can Build Roach Warren?"
        
           
class leaf_build_roach_warren(BTZLeaf):
    
    def execute(self):
        gasY,gasX = (((BTZN().blackboard["obs"]).observation.feature_screen.unit_type == 343 ).nonzero())
        x = random.choice(gasX)
        y = random.choice(gasY)
        if can_do(self,  actions.FUNCTIONS.Build_RoachWarren_screen.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Build_RoachWarren_screen("now", (x, y))
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
    
    def __init__(self):
        self.name = self.name + " Build Roach Warren" 
        
        
        
class leaf_train_roach(BTZLeaf):
    
   
    def execute(self): #assume larva selected
        if can_do(self, actions.FUNCTIONS.Train_Roach_quick.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Train_Roach_quick("now")
        else:
            BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
            

    
    def __init__(self):
        self.name = self.name + "  Train Roach"
        


""" GAS """


class leaf_build_extractor(BTZLeaf):
    
    def execute(self):
        gasY,gasX = (((BTZN().blackboard["obs"]).observation.feature_screen.unit_type == 343 ).nonzero())
        x = random.choice(gasX)
        y = random.choice(gasY)
        if can_do(self, actions.FUNCTIONS.Build_Extractor_screen.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Build_Extractor_screen("now", (x, y))
    
    def __init__(self):
        self.name = self.name + " Build Extractor" 

class leaf_extract_gas(BTZLeaf):
    
    
    def execute(self):
        if (len((get_units_by_type(self, units.Zerg.Extractor))) > 0 and
               can_do(self, actions.FUNCTIONS.Harvest_Gather_screen.id)):
               
            GH = random.choice(get_units_by_type(self, units.Zerg.Extractor))

            BTZN().blackboard["action"] =  actions.FUNCTIONS.Harvest_Gather_screen("now", (GH.x, GH.y))
    
    def __init__(self):
        self.name = self.name + " Harvest Gas"
class selector_larva_to_roach(BTZSelector):

    def decide(self):
        if len( get_units_by_type(self, units.Zerg.Roach)) > 10 :
            self.decision = 1
        else:
            self.decision = 0

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " harvester count"
class selector_count_gas_worker(BTZSelector):
    
    def decide(self):
        if(BTZN().blackboard["harvesters"] > 1):
            self.decision = 1
        else:
            BTZN().blackboard["harvesters"] += 1

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " harvester count"
        
class selector_gas_queen(BTZSelector):
    
    gas1 = False
    gas2 = False
    queen = False
    
    def decide(self):
        if not self.gas1:
            self.decision = 0
            if(len(get_units_by_type(self, units.Zerg.Extractor))>0):
                self.gas1 = True
        elif not self.gas2:
            self.decision = 1
            if(len(get_units_by_type(self, units.Zerg.Extractor))>1):
                self.gas2 = True
        elif not self.queen:
            self.decision = 2
            if (len(get_units_by_type(self, units.Zerg.Queen) ) > 0):
                self.queen = True
        else:
            self.decision = 3
            

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + "Gas Queen"
        
class selector_worker_at_least(BTZSelector):
    
    def decide(self):
        if(len(get_units_by_type(self, units.Zerg.Drone))<18):
            self.decision = 1  #make drone
        else:
            self.decision = 0 # nops
            

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Sweeps"

           
        
        
    
""" MORE MISC """


class selector_sweeps(BTZSelector):
    
    
    def decide(self):
        if BTZN().blackboard["obs"].observation.player.food_used > 100:
            self.decision = 1  #sweeps
        else:
            self.decision = 0 # nops
            

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Sweeps"



class leaf_attack_sweeps(BTZLeaf):
    
    def execute(self):
        if  can_do(self,  actions.FUNCTIONS.Attack_minimap.id):
            BTZN().blackboard["action"] = actions.FUNCTIONS.Attack_minimap("now", (BTZN().blackboard["attack_coords"][0] + random.randint(-10,11),BTZN().blackboard["attack_coords"][1] + random.randint(-10,11)))
        
    def __init__(self):
        self.name = self.name + " Attack Sweeps"
        
class selector_idle_workers(BTZSelector):
    
    def decide(self):
        if (BTZN().blackboard["obs"].observation.player.idle_worker_count > 0):##idle workers
            self.decision = 1
        else:
            self.decision = 0
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Idle Workers"
        
class leaf_select_idle_worker(BTZLeaf):
    
    def execute(self):
        if (can_do(self, actions.FUNCTIONS.select_idle_worker.id)):
            BTZN().blackboard["action"] = actions.FUNCTIONS.select_idle_worker("select")
            
    def __init__(self):
        self.name = self.name + " Select Idle Worker" 
    
"""   NN INTEGREATION STUFF    """

class selector_dummmy_king(BTZSelector):
    
    decree_time = 0
    decree_count = 0
    
    def decide(self):
        if self.decree_time >= 7:
            self.decree_time = 0
            #print("Decree count = ", end = "")
            print(self.decree_count)
            if self.decree_count < 7 :
                self.decision = 0 #opening
                self.decree_count += 1
                
                if BTZN().blackboard["Aspect"] != 0:
                    BTZN().blackboard["switching_aspect"] = 1
                    
            elif self.decree_count % 2 == 0:
                self.decision = 1 #build
                
                if BTZN().blackboard["Aspect"] != 1:
                    BTZN().blackboard["switching_aspect"] = 1
                    
                BTZN().blackboard["Aspect"] = 1
                self.decree_count = random.randint(10, 21)
            else:
                self.decision = 0 #econ
                self.decree_count = random.randint(10, 21)
                
                if BTZN().blackboard["Aspect"] != 2:
                    BTZN().blackboard["switching_aspect"] = 1
                    
                BTZN().blackboard["Aspect"] = 2
        
            print("Aspect = ", end = "")
            print( BTZN().blackboard["Aspect"])
               
        else:
            self.decree_time += 1
            BTZN().blackboard["switching_aspect"] = 0
        ## currently the dummy king cannot attack 
        ##     or scout
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Dummy King"
        

class selector_king_nn(BTZSelector):
    
    
    def decide(self):
        self.decision = BTZN().blackboard["Aspect"] 
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " King Neural Network"
        
class selector_commander_nn(BTZSelector):
    
    def decide(self):
       ##atack location? 
        self.decision = BTZN().blackboard["Aspect"]

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Commander Neural Network"
        

class selector_cam_new_aspect(BTZSelector):
    
    
    def decide(self):

            self.decision = BTZN().blackboard["switching_aspect"] 
            ## 0  ->  carry on
            ## 1  ->  move camera -- maybe other stuff too

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Cam New Aspect"
        
class leaf_cam_aspect(BTZLeaf):
    
    def execute(self):
        print("Aspect = ", end = "")
        print( BTZN().blackboard["Aspect"])
        BTZN().blackboard["Action"] = actions.FUNCTIONS.no_op()
        ## move camera to location:
            ## coords = BTZN().blackboard["aspect_cam_coords"][BTZN().blackboard["Aspect"]]
                ## should be a tuple -- and assigned maybe at obs time? aspect switch time?
        
        BTZLeaf.execute(self)
    def __init__(self):
        self.name = self.name + " Cam Aspect"
        
"""   BUILD TREE UTILITIES   """

class selector_build_decision(BTZSelector):
    
    def decide(self):
        self.decision = BTZN().blackboard["build"] 
        
        if BTZN().blackboard["build"] == 0 :
            print("LING MUTA")
            
        elif BTZN().blackboard["build"] == 1 :
            print("ROACH HYDRA")
            
        elif BTZN().blackboard["build"] == 2 :
            print("MUTA RUPTOR")
        else:
            ##not possible
            print("not possible")
        ## 0 is Ling Muta
        ## 1 is Roach Hydra
        ## 2 is Muta Ruptor
        
        ## 3 is Broodlord Coruptor*
        ## 4 is Ultra Roach*
        
        ## what information should be recieved to swap? -- up to recon? 
        
        ## no-information: random choice is fine -- should only have this choice happen once
        ## discovered: enemey has lots of anti ground -- Muta Ruptor
        ## discovered: enemey has lots of anti air -- Roach Hydra
        ## discovered: enemey has lots of anti ground -- muta ruptor

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Build Decision"
    
class selector_build_progression(BTZSelector):


    alternator = 0
    split = [12,4,4]
    tech_done = 0
    upgrades_done = 0
    
    def decide(self):
        build = BTZN().blackboard["build"]
        #print(self.alternator)
        print(self.split)
        self.tech_done = BTZN().blackboard["tech_done"][build]
        self.upgrades_done = BTZN().blackboard["upgrades_done"][build]
        
        
            
        if BTZN().blackboard["phase"] < self.split[0]:
            self.decision = 0 #tech
        elif BTZN().blackboard["phase"] <= self.split[1]+self.split[0]:
            self.decision = 1 #upgrades
        elif BTZN().blackboard["phase"] <= sum(self.split):
            self.decision = 2
        else:
            BTZN().blackboard["phase"] = 0
            
        BTZN().blackboard["phase"] += 1
        
        if not self.upgrades_done and self.tech_done:
            self.split = [0,6,14]
        elif self.upgrades_done and not self.tech_done:
            self.split = [6,0,4]
        elif self.upgrades_done and self.tech_done:
            self.split = [2,0,30]
        else:
            self.split = [12,4,4]
        
        ## 0 is Tech Buildings
            ## coords are gonna be important
        ## 1 is Upgrades
            ## this can serve as a check for making sure the buildings exist
            ## "check off" upgrades in aropriate BB slot    
        ## 2 is Production
            ## although this is the branch that should be run the most 
            ## it may have some of the lowest priority?
            ## cylcle bases, produce units
            
        ## what information should be recieved to swap?
        
        ## if we have yet to build necesarry buildings  -- tech
        ## if we move screen to coords of specfic tech building and find it not to exist -- tech
        ## upgrades as necesaryy?
        ## possibly a 3 - 1 - 1 split to start
        ## then when build is done  0 - 3 - 7
        ## then when upgrades done  1 - 0 - 19 maybe higher?
        
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Build Progression Alternator"        

""" BUILD TECH """

class selector_tech_progression_LM(BTZSelector):
    
    ##sp
    ##evo
    ##lair
    ##spire
    
    def decide(self):
        if BTZN().blackboard["tech_buildings"]["spawning_pool"][0] == -1:
            self.decision = 0
            BTZN().blackboard["tech_done"][0] = 0
        elif BTZN().blackboard["tech_buildings"]["evolution_chamber"][0] == -1:
            self.decision = 1
            BTZN().blackboard["tech_done"][0] = 0
        elif BTZN().blackboard["upgrades"]["lair"] == 0:
            self.decision = 2
            BTZN().blackboard["tech_done"][0] = 0
        elif BTZN().blackboard["tech_buildings"]["spire"][0] == -1:
            self.decision = 3
            BTZN().blackboard["tech_done"][0] = 0
        else:
            self.decision = 4 ## check or nop for now
            BTZN().blackboard["tech_done"][0] = 1
            
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Tech Progression Ling Muta"        

class selector_tech_progression_RH(BTZSelector):
    
    ##sp
    ##rw
    ##evo
    ##lair
    ##hd
    
    def decide(self):
        if BTZN().blackboard["tech_buildings"]["spawning_pool"][0] == -1:
            self.decision = 0
            BTZN().blackboard["tech_done"][1] = 0
        elif BTZN().blackboard["tech_buildings"]["roach_warren"][0] == -1:
            self.decision = 1
            BTZN().blackboard["tech_done"][1] = 0
        elif BTZN().blackboard["upgrades"]["lair"] == 0:
            self.decision = 2
            BTZN().blackboard["tech_done"][1] = 0
        elif BTZN().blackboard["tech_buildings"]["evolution_chamber"][0] == -1:
            self.decision = 3
            BTZN().blackboard["tech_done"][1] = 0
        elif BTZN().blackboard["tech_buildings"]["hydralisk_den"][0] == -1:
            self.decision = 4
            BTZN().blackboard["tech_done"][1] = 0
        else:
            self.decision = 5 ## check
            BTZN().blackboard["tech_done"][1] = 1
            
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Tech Progression Roach Hydra"   

class selector_tech_progression_MR(BTZSelector):
    
    ##sp
    ##lair
    ##spire
    ##spire2
    
    def decide(self):
        if BTZN().blackboard["tech_buildings"]["spawning_pool"][0] == -1:
            self.decision = 0
            BTZN().blackboard["tech_done"][2] = 0
        elif BTZN().blackboard["tech_buildings"]["lair"][0] == -1:
            self.decision = 1
            BTZN().blackboard["tech_done"][2] = 0
        elif BTZN().blackboard["tech_buildings"]["spire"][0] == -1:
            self.decision = 2
            BTZN().blackboard["tech_done"][2] = 0
        else:
            self.decision = 3 ## check
            BTZN().blackboard["tech_done"][2] = 1 #done
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Tech Progression Muta Ruptor"   
        
        
""" BUILD UPGRADES """

class selector_upgrade_tech_exists(BTZSelector): #tech does not exist, recet its build values and nop
    
    unit_type = 0
    tech_name = ""
    
    def decide(self):
        if len(get_units_by_type(self, self.unit_type)) > 0:
            self.decision = 0
        else:
            self.decision = 1 ## not there
            BTZN().blackboard["tech_buildings"][self.tech_name][0] = -1
            BTZN().blackboard["tech_buildings"][self.tech_name][0] = -1
            BTZN().blackboard["tech_done"][BTZN().blackboard["build"]] = 0 #not done
    
    def __init__(self, decendant, unit_type, tech_name):
        self.children = decendant
        self.unit_type = unit_type
        self.tech_name = tech_name
        self.name = self.name + " Upgrade Tech Check"
    
class selector_can_uprade(BTZSelector): # can't for whatever reason, so nop 
    
    action = 0
    def decide(self):
        if can_do(self, self.action):
            self.decision = 0 ## can
        else:
            self.decision = 1 ## cant
    
    def __init__(self, decendant, action):
        self.children = decendant
        self.action = action
        self.name = self.name + " Can Upgrade?"

class leaf_start_upgrade(BTZLeaf): # action and set to -1, set timer sas well?
    
    action = 0
    upgrade_name = ""
    action_id = 0
    def execute(self):
        if can_do(self, self.action_id):
            BTZN().blackboard["action"] = self.action
            BTZN().blackboard["upgrade_timer"][self.upgrade_name][0] = BTZN().blackboard["time"] + 50
            BTZN().blackboard["upgrade_timer"][self.upgrade_name][1] = BTZN().blackboard["upgrades"][self.upgrade_name] + 1
            BTZN().blackboard["upgrades"][self.upgrade_name] = -1
        
    def __init__(self, action, action_id, upgrade_name):
        self.action = action
        self.upgrade_name = upgrade_name
        self.action_id = action_id
        self.name = self.name + " Start Upgrade"    
    

class decorator_upgrade_timer(BTZDecorator): # -1 to +num

    def execute(self):
        for upgrade_name in BTZN().blackboard["upgrade_timer"]: # may error?
            if BTZN().blackboard["upgrades"][upgrade_name] == -1:
                if BTZN().blackboard["time"] >= BTZN().blackboard["upgrade_timer"][upgrade_name][0]:
                    BTZN().blackboard["upgrades"][upgrade_name] = BTZN().blackboard["upgrade_timer"][upgrade_name][1]
                    
        BTZDecorator.execute(self)
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Upgrade Timer"
     

class selector_upgrade_progression_LM(BTZSelector):
    
    ##mb
    ##ga1
    ##aa1
    ##ga2
    ##aa2
    ##gm1
    ##ar1
    ##gm2
    ##ar2
    
    def decide(self):
        if (BTZN().blackboard["upgrades"]["metabolic_boost"] != 1
        and BTZN().blackboard["upgrades"]["metabolic_boost"] != -1):
            self.decision = 0
        elif (BTZN().blackboard["upgrades"]["ground_armor"] != 2 
        and BTZN().blackboard["upgrades"]["ground_armor"] != -1):
            self.decision = 1
        elif (BTZN().blackboard["upgrades"]["air_armor"] != 2
        and BTZN().blackboard["upgrades"]["air_armor"] != -1):
            self.decision = 2
        elif (BTZN().blackboard["upgrades"]["ground_melee"] != 2
        and BTZN().blackboard["upgrades"]["ground_melee"] != -1):
            self.decision = 3
        elif (BTZN().blackboard["upgrades"]["air_ranged"] != 2
        and BTZN().blackboard["upgrades"]["air_ranged"] != -1):
            self.decision = 4
        elif (BTZN().blackboard["upgrades"]["metabolic_boost"] == 1
        and BTZN().blackboard["upgrades"]["ground_armor"] == 2
        and BTZN().blackboard["upgrades"]["air_armor"] == 2
        and BTZN().blackboard["upgrades"]["ground_melee"] == 2
        and BTZN().blackboard["upgrades"]["air_ranged"] == 2):
            self.decision = 5 ## check
            BTZN().blackboard["upgrades_done"][0] = 1
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Upgrade Progression Ling Muta"        

class selector_upgrade_progression_RH(BTZSelector):
    
    ##ma
    ##gs
    ##gr1
    ##gr2
    ##ga1
    ##ga2
    
    def decide(self):
        if (BTZN().blackboard["upgrades"]["muscular_augments"] != 1
        and BTZN().blackboard["upgrades"]["muscular_augments"] != -1):
            self.decision = 0
        elif (BTZN().blackboard["upgrades"]["grooved_spines"] != 1 
        and BTZN().blackboard["upgrades"]["grooved_spines"] != -1):
            self.decision = 1
        elif (BTZN().blackboard["upgrades"]["ground_armor"] != 2
        and BTZN().blackboard["upgrades"]["ground_armor"] != -1):
            self.decision = 2
        elif (BTZN().blackboard["upgrades"]["ground_ranged"] != 2
        and BTZN().blackboard["upgrades"]["ground_ranged"] != -1):
            self.decision = 3
        elif (BTZN().blackboard["upgrades"]["muscular_augments"] == 1
        and BTZN().blackboard["upgrades"]["ground_armor"] == 2
        and BTZN().blackboard["upgrades"]["grooved_spines"] == 1
        and BTZN().blackboard["upgrades"]["ground_ranged"] == 2):
            self.decision = 4 ## check
            BTZN().blackboard["upgrades_done"][1] = 1
            
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Upgrade Progression Roach Hydra"   

class selector_upgrade_progression_MR(BTZSelector):
    
    ##aa1
    ##ar1
    ##aa2
    ##ar2
    
    def decide(self):
        
        if (BTZN().blackboard["upgrades"]["air_ranged"] != 2
        and BTZN().blackboard["upgrades"]["air_ranged"] != -1):
            self.decision = 0
        elif (BTZN().blackboard["upgrades"]["air_armor"] != 2
        and BTZN().blackboard["upgrades"]["air_armor"] != -1):
            self.decision = 1
        elif (BTZN().blackboard["upgrades"]["air_armor"] == 2
        and BTZN().blackboard["upgrades"]["air_ranged"] == 2):
            self.decision = 2 ## check
            BTZN().blackboard["upgrades_done"][2] = 1
            
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Upgrade Progression Muta Ruptor"

""" BUILD UNIT PRODUCTION """

class selector_production_ratio_controller(BTZSelector):
    
    
    unit_type_one = None
    unit_type_two = None
    unit_ratio = 1
    
    def decide(self):
        if (BTZN().blackboard["army_unit_counts"][self.unit_type_one]/(BTZN().blackboard["army_unit_counts"][self.unit_type_two] + 1)  <= self.unit_ratio):
            self.decision = 0 ## produce unit type one
        else:
            self.decision = 1 ## produce unit type two

        

    def __init__(self, decendant, unit_type_one, unit_type_two, unit_ratio):
        self.children = decendant
        self.unit_type_one = unit_type_one
        self.unit_type_two = unit_type_two
        self.unit_ratio = unit_ratio
        self.name = self.name + " Production Ratio Controller"
    
    
    
class selector_fake_production_ratio_controller(BTZSelector):
    
    
    unit_type_one = None
    unit_type_two = None
    unit_ratio = 1
    
    def decide(self):
        if random.randint(0,50) % 2:
            self.decision = 0 ## produce unit type one
        else:
            self.decision = 1 ## produce unit type two

        

    def __init__(self, decendant, unit_type_one, unit_type_two, unit_ratio):
        self.children = decendant
        self.unit_type_one = unit_type_one
        self.unit_type_two = unit_type_two
        self.unit_ratio = unit_ratio
        self.name = self.name + " Fake Production Ratio Controller"
        
class decorator_print_army(BTZDecorator):
    def execute(self):
        print("owhqer")
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Upgrade Timer"
