'''
Created on Feb 11, 2019

@author: Daniel
'''
class BeTrNode:
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
    
    def noop(self):
        print(self.name)


    def __init__(self):
        '''
        Constructor
        '''
class BeTrRoot(BeTrNode):
    
    name = "Root"
    
    children = []
    
    def execute(self):
        if BeTrNode().blackboard.get("root") == BeTrNode().blackboard.get("current_sequence"):
            list(map(lambda x:x.execute(),self.children))

        else:
            list(map(lambda x:x.execute(),[BeTrNode().blackboard.get("current_sequence")]))

            
    def noop(self):
        print(self.name)
        
    def __init__(self, decendant):
        self.children = decendant
        BeTrNode().blackboard.update({"root" : self,
                               "current_node" : self,
                               "current_sequence" : self})
        
class BeTrLeaf(BeTrNode):
    
    name = "Leaf"
    
    children = None
    
    def execute(self):
        pass 
    
    
    def __init__(self):
        pass
    
class BeTrDeco(BeTrNode):
    
    name = "Decorator"
    
    children = []
    
    def execute(self):
        list(map(lambda x:x.execute(),self.children))
    
    
    def __init__(self, decendant):
        self.children = decendant
    
    
        
class BeTrSelector(BeTrNode):
    
    name = "Selector"
    
    children = []
    
    decision = 0
    
    
    def execute(self):
        self.decide()
        if self.decision in range(0,len(self.children)):
            list(map(lambda x:x.execute(),[self.children[self.decision]]))
        else:
            self.noop()
        
    def decide(self):
        raise NotImplementedError
        
    def __init__(self, decendant):
        self.children = decendant

        
class BeTrSequence(BeTrNode):
    
    name = "Sequence"
    
    children = []
    
    next_child = 0
    
    previous_sequence = None
    
    def setup(self):
        self.previous_sequence = BeTrNode().blackboard.get("current_sequence")
        BeTrNode().blackboard["current_sequence"] = self
        
    def execute(self):
        if self.next_child == 0:
            self.setup()
        if self.next_child in range(0,len(self.children)-1):
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child+=1
        else:
            BeTrNode().blackboard["current_sequence"] = self.previous_sequence
            list(map(lambda x:x.execute(),[self.children[self.next_child]]))
            self.next_child = 0
            
        
    def __init__(self, decendant):
        self.children = decendant
        
    
    
    