'''
Created on Feb 11, 2019

@author: Daniel
'''
from BeTr import BeTrLeaf, BeTrSequence, BeTrSelector, BeTrNode, BeTrDeco

class leaf_hello(BeTrLeaf):
    
    def execute(self):
        print("Hello")

        
    def __init__(self):
        
        self.name = self.name + " Hello" 
    
class leaf_running(BeTrLeaf):
    
    count = 1;
    
    def execute(self):
        print("I am Executing", end=" ")
        print("Round: ", self.count)
        self.count +=1
        
    def __init__(self):
        
        self.name = self.name + " Running" 
        
class leaf_goodbye(BeTrLeaf):

    def execute(self):
        print("Goodbye")
        
    def __init__(self):
        
        self.name = self.name + " Goodbye" 
        
class leaf_subtask(BeTrLeaf):
    
    count = 1;
    
    def execute(self):
        print("I am a subtask", end=" ")
        print("iter: ", self.count)
        if self.count == 10:
            BeTrNode().blackboard["direction"] = "up"
        self.count +=1
           
    def __init__(self):
        
        self.name = self.name + " Subbing" 
        
class selector_LR(BeTrSelector):
    
    def decide(self):
        if BeTrNode().blackboard.get("direction") == "left":
            self.decision = 0
            BeTrNode().blackboard["direction"] = "right"
        elif BeTrNode().blackboard.get("direction") == "right":
            self.decision = 1
            BeTrNode().blackboard["direction"] = "left"
        else:
            self.decision = -1
        
   
    
    def __init__(self, decendant):
        self.children = decendant
        BeTrNode().blackboard["direction"] = "left"
        self.name = self.name + " Choosing" 
        
class decorator_flowers(BeTrDeco):
    
    def execute(self):
        print("flower", end=" ")
        list(map(lambda x:x.execute(),self.children))
        print(" flower", end="")
    
    def __init__(self, decendant):
        self.children = decendant
        self.name = self.name + " Flowers"
    