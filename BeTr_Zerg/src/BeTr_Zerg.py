'''
Created on Feb 11, 2019

@author: Daniel

'''

from pysc2.lib import actions




class BTZN:
    '''
    classdocs
    '''
    blackboard = {}
    
    @property
    def name(self):
        raise NotImplementedError
    
    @property
    def children(self):
        raise NotImplementedError    
    
    def execute(self):
        pass
    
    
    def printName(self):
        print(self.name)

    def __init__(self):
        '''
        Constructor
        '''
class BTZRoot(BTZN):
    
    name = "Root"
    
    children = []
    
    def execute(self,obs):
        BTZN().blackboard["obs"] = obs 
        BTZN().blackboard["time"] = BTZN().blackboard["time"] + 1 #probably a bad idea   
        BTZN().blackboard["action"] = actions.FUNCTIONS.no_op()
        list(map(lambda x:x.execute(),self.children))
        
        
        ## OLD SEQ EXECUTION STUFF
        #if BTZN().blackboard.get("root") == BTZN().blackboard.get("current_sequence"):
        #    list(map(lambda x:x.execute(),self.children))

        #else:
        #    list(map(lambda x:x.execute(),[BTZN().blackboard.get("current_sequence")]))

            
    def printName(self):
        print(self.name)
        
    def setup(self, obs):
        (BTZN().blackboard["obs"]) = obs
    
    def act(self):
        return BTZN().blackboard["action"]
    
    def write(self, key, value):
        BTZN().blackboard[key] = value
        
    def __init__(self, decendant):
        self.children = decendant
        BTZN().blackboard.update({"root" : self,
                                "current_node" : self,
                                "obs" : None,
                                "action" : actions.FUNCTIONS.no_op(),
                                
                                "Aspect_sub_roots" : [None,None,None,None],
                                "Aspect_current_sequences" : [None,None,None,None],
                                "aspect_cam_coords" : [], #should be list of tuples relative to minimap
                                "tech_buildings" : {"spawning_pool" : [-1,-1], #minimap locations
                                                 "roach_warren" : [-1,-1],
                                                 "lair" : [-1,-1],
                                                 "spire" : [-1,-1],
                                                 "evolution_chamber" : [-1,-1],
                                                 "spire" : [-1,-1],
                                                 "spire_2" : [-1,-1],
                                                 "hydralisk_den" : [-1,-1],
                                                 },
                                "upgrades" : {"metabolic_boost" : 0, # 0 means none, -1 means in progress?
                                                "ground_armor" : 0,
                                                "ground_ranged" : 0,
                                                "ground_melee" : 0,
                                                "muscular_augments" : 0,
                                                "grooved_spines" : 0,
                                                "air_armor" : 0,
                                                "air_ranged" : 0,
                                                "lair" : 0
                                                 },
                                "upgrade_timer" :{"metabolic_boost" : [0,0], ## [0] is time, [1] is next num
                                                 "ground_armor" : [0,0],
                                                 "ground_ranged" : [0,0],
                                                 "ground_melee" : [0,0],
                                                 "muscular_augments" : [0,0],
                                                 "grooved_spines" : [0,0],
                                                 "air_armor" : [0,0],
                                                 "air_ranged" : [0,0],
                                                 "lair" : [0,0]
                                                },
                                
                                
                                
                            ###### BELOW HERE ARE VALUES FOR THE NN INPUTS ######
                                
                               
                                "time" : 0,
                                "opening" : 1, # randomly chosen opening
                                "build" : 0, # current build choice
                                "phase" : 0, # which part of build
                                "base_top_left" : 0,
                                "hatcheries" : [],
                                "army_unit_counts" : {},#change to troops later
                                "Aspect" : 0,
                                "switching_aspect" : 0,
                                "tech_done" : [0,0,0],
                                "upgrades_done" : [0,0,0],
                                "troops" : {"105": 0, "110": 0, "108": 0, "112": 0, "107": 0},
                                ## also all the scout and army stuff to be added
                                

})
        
        
class BTZAspect(BTZN):
    
    name = "Aspect"
    aspect = 0
    children = []
    
    def execute(self):
        if BTZN().blackboard["Aspect_sub_roots"][self.aspect] == BTZN().blackboard["Aspect_current_sequences"][self.aspect]:
            list(map(lambda x:x.execute(),self.children))

        else:
            list(map(lambda x:x.execute(),[BTZN().blackboard["Aspect_current_sequences"][self.aspect]]))

    def __init__(self):
        pass
        
class BTZLeaf(BTZN):
    
    name = "Leaf"
    
    children = None
    
    def execute(self):
        pass 
    
    
    def __init__(self):
        pass
    
class BTZDecorator(BTZN):
    
    name = "Decorator"
    
    children = []
    
    def execute(self):
        list(map(lambda x:x.execute(),self.children))
    
    
    def __init__(self, decendant):
        self.children = decendant
    
    
        
class BTZSelector(BTZN):
    
    name = "Selector"
    
    children = []
    
    decision = 0
    
    
    def execute(self):
        self.decide()
        if self.decision in range(0,len(self.children)):
            list(map(lambda x:x.printName(),[self.children[self.decision]]))
            
            list(map(lambda x:x.execute(),[self.children[self.decision]]))
            
        else:
            self.printName()
        
    def decide(self):
        raise NotImplementedError
        
    def __init__(self, decendant):
        self.children = decendant
        
class BTZSmartSelector(BTZN):
    
    name = "Smart Selector"
    
    children = []
    
    decision = 0
    
    
    def execute(self):
        self.decide()
        if self.decision in range(0,len(self.children)):
            #list(map(lambda x:x.printName(),[self.children[self.decision]]))
            
            list(map(lambda x:x.execute(),[self.children[self.decision]]))
            
        else:
            self.printName()
        
    def decide(self):
        raise NotImplementedError
    
    def learn(self):
        raise NotImplementedError
    
    def setup(self):
        raise NotImplementedError
        
    def __init__(self, decendant):
        self.children = decendant

        
class BTZSequence(BTZN):
    
    name = "Sequence"
    
    children = []
    
    next_child = 0
    
    previous_sequence = None
    
    def setup(self):
        self.previous_sequence = BTZN().blackboard["Aspect_current_sequences"][BTZN().blackboard["Aspect"]]
        BTZN().blackboard["Aspect_current_sequences"][BTZN().blackboard["Aspect"]] = self
        
    def execute(self):
        if self.next_child == 0:
            self.setup()
        if self.next_child in range(0,len(self.children)-1):
            list(map(lambda x:x.printName(),[self.children[self.next_child]]))
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child+=1
        else:
            BTZN().blackboard["Aspect_current_sequences"][BTZN().blackboard["Aspect"]] = self.previous_sequence
            list(map(lambda x:x.printName(),[self.children[self.next_child]]))
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child = 0
            
        
    def __init__(self, decendant):
        self.children = decendant
        
    
    
    