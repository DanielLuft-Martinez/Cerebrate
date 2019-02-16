'''
Created on Feb 13, 2019

@author: Daniel
'''
from pysc2.tests import dummy_observation
from pysc2.tests.dummy_observation import Builder
from pysc2.lib import features
from pysc2.lib import point
from pysc2.lib import actions
from pysc2.lib import units

from s2clientprotocol import common_pb2



class my_dumb_obs(object):
    '''
    classdocs
    '''
    single_select =[]
    multi_select=[]
    build_queue=[]
    cargo=[]
    cargo_slots_available=[]
    feature_screen=[]
    feature_minimap=[]
    last_actions=[]
    action_result=[]
    alerts=[]
    game_loop=[]
    score_cumulative=[]
    player=[]
    control_groups=[]
    feature_units=[]
    available_actions=[]
    
     
    def observation(self):
        return self

    def __init__(self):
        '''
        Constructor
        '''
        