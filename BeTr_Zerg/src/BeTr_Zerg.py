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
        if BTZN().blackboard.get("root") == BTZN().blackboard.get("current_sequence"):
            list(map(lambda x:x.execute(),self.children))

        else:
            list(map(lambda x:x.execute(),[BTZN().blackboard.get("current_sequence")]))

            
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
                               "current_sequence" : self,
                               "obs" : None,
                               "action" : actions.FUNCTIONS.no_op(),
                               "time" : 0,
                               "base_top_left" : 0,
                               "hatcheries" : {},
                               "army_unit_counts" : {}, 
                               })
        
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
            #list(map(lambda x:x.printName(),[self.children[self.decision]]))
            
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
        self.previous_sequence = BTZN().blackboard.get("current_sequence")
        BTZN().blackboard["current_sequence"] = self
        
    def execute(self):
        if self.next_child == 0:
            self.setup()
        if self.next_child in range(0,len(self.children)-1):
            #list(map(lambda x:x.printName(),[self.children[self.next_child]]))
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child+=1
        else:
            BTZN().blackboard["current_sequence"] = self.previous_sequence
            #list(map(lambda x:x.printName(),[self.children[self.next_child]]))
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child = 0
            
        
    def __init__(self, decendant):
        self.children = decendant
        
    
    
    