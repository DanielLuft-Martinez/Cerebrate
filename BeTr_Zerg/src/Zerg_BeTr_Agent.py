from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import BeTr_Zerg
import nodes_BeTr_Zerg
import random
from nodes_BeTr_Zerg import leaf_select_drone_random, leaf_action_noop,\
    decorator_step_obs, leaf_build_spawning_pool, selector_spawning_pool_exist,\
    selector_can_build_spawning_pool, selector_supply, leaf_select_unit_random,\
    leaf_train_overlord, leaf_train_drone, leaf_train_zergling, leaf_train_queen,\
    selector_queen_upkeep, selector_build_phase, leaf_queen_inject_larva,\
    decorator_phase, leaf_select_unit_all, selector_ling_attack_wave,\
    leaf_attack, leaf_select_army
from BeTr_Zerg import BTZSequence, BTZRoot


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
            
            if xmean <= 31 and ymean <= 31:
                self.root.write("attack_coords", (49, 49))
            else:
                self.root.write("attack_coords", (12, 16))
                
                
        self.root.execute(obs)
    #   print(self.root.act())
        return self.root.act()       

        
    def build_tree(self):
        get_drone = leaf_select_drone_random();
        nop = leaf_action_noop()
        bsp = leaf_build_spawning_pool()
        
        sp_can = selector_can_build_spawning_pool([bsp,nop])
        
        sp_seq = BTZSequence([get_drone, sp_can])
        
        select_larva = leaf_select_unit_random(units.Zerg.Larva)
        
        
        queen_upkeep = BTZSequence([leaf_select_unit_random(units.Zerg.Queen),leaf_queen_inject_larva()])
        
        
        trn_drn = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_drone()])
        trn_ling = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_zergling()])
        trn_OL = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_overlord()])
        trn_queen = BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery),leaf_train_queen()])
        
        trn_ling_all = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_zergling()])
        
        #sply = selector_supply([trn_OL,])
        
        prep = selector_queen_upkeep([queen_upkeep,selector_supply([trn_OL,trn_ling])])
        
        launch = leaf_attack()
        
        send = BTZSequence([leaf_select_army(),launch])
        
        wave = selector_ling_attack_wave([selector_supply([trn_OL,trn_ling_all]),send])
        
        attack = selector_queen_upkeep([queen_upkeep,wave])
        
        build = selector_spawning_pool_exist([sp_seq,trn_queen])
        
        opening = selector_build_phase([build, prep, attack])
        
        phase = decorator_phase([opening])
       
        observe = decorator_step_obs([phase])
        
        self.root = BTZRoot([observe])     
    
    
def main(unused_argv):
    agent = ZergAgent()
    try:
        while True:
            with sc2_env.SC2Env(map_name="Catalyst", players=[sc2_env.Agent(sc2_env.Race.zerg), sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)],
                agent_interface_format=features.AgentInterfaceFormat(feature_dimensions=features.Dimensions(screen=84, minimap=64),use_feature_units=True),
                      step_mul=16,
                      game_steps_per_episode=0,
                      visualize=True) as env:
                      
                agent.setup(env.observation_spec(), env.action_spec())
                    
                timesteps = env.reset()
                agent.reset()
                    
                while True:
                    step_actions = [agent.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps = env.step(step_actions)
                  
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)
