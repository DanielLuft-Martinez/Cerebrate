'''
Created on Feb 11, 2019

@author: Daniel
'''
import BeTr

from BeTr_Test import leaf_hello, leaf_running, leaf_goodbye, leaf_subtask,\
    selector_LR, decorator_flowers
from BeTr import BeTrRoot, BeTrSequence

def main():
    print("main:")
    hello = leaf_hello()
    running = leaf_running()
    goodbye = leaf_goodbye()
    sub1 = leaf_subtask()
    sub2 = leaf_subtask()
    
    
    
    seq1 = BeTrSequence([hello,running,running,running,running,goodbye])
    
    
    seq2 = BeTrSequence([sub1,sub1,sub1])
    
    seq3 = BeTrSequence([sub2,seq2,sub2])
    
    sel = selector_LR([seq1,seq3])
    
    #dec = decorator_flowers([sel])
    
    #seq = BeTrSequence([seq1,seq3])
    
    root = BeTrRoot([sel])
    
    for i in range(0,100):
        print(i,end = ": ")
        root.execute()
   
 
 
    
    

if __name__ == '__main__':
    main()
    