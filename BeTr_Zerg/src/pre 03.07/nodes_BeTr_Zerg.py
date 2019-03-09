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


def get_units_by_type(self,  unit_type):
    obs =  BTZN().blackboard["obs"]
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
            self.spawning_pools = [1]
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
        
        
""" Roach Warren SEQUENCE """

class selector_roach_opening_phase(BTZSelector):
    attacking = False
    def decide(self):#build
        if self.attacking :
            self.decision = 2 #attack
            #print("ATTACK")
        elif (len(get_units_by_type(self, units.Zerg.RoachWarren)) >= 1  
            and len(get_units_by_type(self, units.Zerg.Extractor)) > 1 
            and len(get_units_by_type(self, units.Zerg.Queen)) >= 1 
            and not self.attacking ):
            self.decision = 1 #prep
            #print("PREP")
            #print("PREP")
            if len(get_units_by_type(self, units.Zerg.Roach))>2:
                self.attacking =True
            
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Roach Opening Phase"
        
class selector_roach_opening_build(BTZSelector):
    
    def decide(self):
        if (len(get_units_by_type(self, units.Zerg.RoachWarren)) <= 0  
            and len(get_units_by_type(self, units.Zerg.Extractor)) <= 0 
            and len(get_units_by_type(self, units.Zerg.Queen)) <= 0) :
            self.decision = 0 #build
            #print("BUILD")
        elif len(get_units_by_type(self, units.Zerg.Roach)) < 5:
            self.decision = 1 #prep
           # print("PREP")
        else:
            self.decision = 2 #attack
            #print("ATTACK")
        
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Roach Opening Build"

class selector_roach_warren_exist(BTZSelector):
    
    def decide(self):
        
        if len(get_units_by_type(self, units.Zerg.RoachWarren)) == 0:
            self.decision = 0 #does not have sp - 0 is build sp sequence
            self.roach_warrens = [1]
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
            
            if self.decree_count < 10 :
                self.decision = 0 #opening
                self.decree_count += 1
                
                if BTZN().blackboard["Aspect"] != 0:
                    BTZN().blackboard["swaspect"] = 1
                    
            elif self.decree_count % 2 == 0:
                self.decision = 1 #build
                
                if BTZN().blackboard["Aspect"] != 1:
                    BTZN().blackboard["swaspect"] = 1
                    
                BTZN().blackboard["Aspect"] = 1
                self.decree_count = random.randint(10, 21)
            else:
                self.decision = 0 #econ
                self.decree_count = random.randint(10, 21)
                
                if BTZN().blackboard["Aspect"] != 2:
                    BTZN().blackboard["swaspect"] = 1
                    
                BTZN().blackboard["Aspect"] = 2
                
            
        else:
            self.decree_time += 1
            BTZN().blackboard["swaspect"] = 0
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

            self.decision = BTZN().blackboard["swaspect"] 
            ## 0  ->  carry on
            ## 1  ->  move camera -- maybe other stuff too

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Cam New Aspect"
        


        
"""   BUILD TREE UTILITIES   """

class selector_build_decision(BTZSelector):
    
    def decide(self):
        self.decision = BTZN().blackboard["Build"] 
        ## 0 is Ling Muta
        ## 1 is Roach Hydra
        ## 2 is Muta Ruptor
        
        ## 3 is Broodlord Coruptor*
        ## 4 is Ultra Roach*S
        
        ## what information should be recieved to swap? -- up to recon? 
        
        ## no-information: random choice is fine -- should only have this choice happen once
        ## discovered: enemey has lots of anti ground -- Muta Ruptor
        ## discovered: enemey has lots of anti air -- Roach Hydra
        ## discovered: enemey has lots of anti ground -- muta ruptor

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Build Decision"
    
class selector_build_progression_alternator(BTZSelector):

    def decide(self):
        self.decision = BTZN().blackboard["Build"] 
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
        ## then when build is done  1 - 2 - 7
        ## then when upgrades done  1 - 0 - 9 maybe higher?
        
        

    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Build Progression Alternator"        

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
    
    
    
    
    
