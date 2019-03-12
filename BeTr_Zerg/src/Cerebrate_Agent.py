from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.env.run_loop import run_loop
from pysc2.lib import actions, features, units
from absl import app
import Zerg_Gas_Agent
import BeTr_Zerg
import nodes_BeTr_Zerg
import random
from nodes_BeTr_Zerg import *
from BeTr_Zerg import BTZSequence, BTZRoot
from Cerebrate_Tree import *


class ZergAgent(base_agent.BaseAgent):
    

    
    root = BTZRoot([])
    
     

    def __init__(self):
        super(ZergAgent, self).__init__()            

            
        self.gas_harvesters = 0
        
        self.attack_coordinates = None
        

    
    
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
    
    
    def step(self, obs):
        
        
        super(ZergAgent, self).step(obs)
        
        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative == 
            features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()
            
            self.build_tree()
            self.root.setup(obs)
            
            self.gas_harvesters = 0
            #self.root.write("opening", (random.randint(0, 10) % 2))
            #self.root.write("build", (random.randint(0, 30) % 3))
            self.root.write("opening", 1)
            self.root.write("build", 1)
            self.root.write("harvesters", 0)
            
            self.root.write("hatcheries",{"main" : (xmean,ymean)})
            
            
            if xmean <= 31 and ymean <= 31:
                self.root.write("attack_coords", (49, 49))
                self.root.write("base_top_left", 1)
            else:
                self.root.write("attack_coords", (12, 16))
                
                
        self.root.execute(obs)
    #   print(self.root.act())
        return self.root.act()       

        
    def build_tree(self):
        
        self.root = CerebrateTree.build_tree(self)     
       
    
    
def main(unused_argv):
    agent1 = ZergAgent()
    #agent2 = Zerg_Gas_Agent.ZergGasAgent() # sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)
    try:
        while True:# sc2_env.Agent(sc2_env.Race.zerg)
            with sc2_env.SC2Env(map_name="Catalyst", players=[sc2_env.Agent(sc2_env.Race.zerg), sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)],
                agent_interface_format=features.AgentInterfaceFormat(feature_dimensions=features.Dimensions(screen=84, minimap=64),use_feature_units=True),
                      step_mul=16,
                      game_steps_per_episode=0,
                      visualize=False) as env:
                
                run_loop([agent1], env)
                    
                  
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)
