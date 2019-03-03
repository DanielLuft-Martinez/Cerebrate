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
            self.root.write("opening", 1)
            self.root.write("harvesters", 0)
            
            
            if xmean <= 31 and ymean <= 31:
                self.root.write("attack_coords", (49, 49))
                self.root.write("base_top_left", 1)
            else:
                self.root.write("attack_coords", (12, 16))
                
                
        self.root.execute(obs)
    #   print(self.root.act())
        return self.root.act()       

        
    def build_tree(self):
        
        """ Queen Ling open """
        get_drone = leaf_select_drone_random();
        nop = leaf_action_noop()
        bsp = leaf_build_spawning_pool()
        
        sp_can = selector_can_build_spawning_pool([bsp,nop])
        
        sp_seq = BTZSequence([get_drone, sp_can])
        
        select_larva = leaf_select_unit_random(units.Zerg.Larva)
        
        trn_queen = BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery),leaf_train_queen()])
        
        
        queen_upkeep = selector_has_queen_upkeep([BTZSequence([leaf_select_unit_random(units.Zerg.Queen),leaf_queen_inject_larva()]), trn_queen])
        
        shift_OL = selector_shift_overlord_cloud([leaf_shift_overlord_cloud(), nop ])
        
        trn_drn = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_drone()])
        trn_ling = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_zergling()])
        trn_OL = BTZSequence([leaf_select_unit_random(units.Zerg.Larva),leaf_train_overlord(), leaf_select_unit_all(units.Zerg.Overlord), shift_OL])
       
        trn_ling_all = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_zergling()])
        
        #sply = selector_supply([trn_OL,])
        drn_OL =  selector_supply([trn_OL, trn_drn])
        
        
        prep = selector_queen_upkeep([queen_upkeep,selector_supply([trn_OL,trn_ling])])
        
        launch = leaf_attack()
        
        send = BTZSequence([leaf_select_army(),launch])
        
        wave = selector_supply([trn_OL, selector_ling_attack_wave([selector_supply([trn_OL,trn_ling_all]),send])])
        
        attack = selector_queen_upkeep([queen_upkeep,wave])
        
        build = selector_spawning_pool_exist([sp_seq,trn_queen])
        
        opener_Qling = selector_build_phase([build, prep, attack])
        
        phase_Qling = decorator_phase_queen_ling([opener_Qling])
        
        """ Queen Roach open """
        set_wp = BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery), leaf_simple_waypoint_close()])
        
        trn_roach = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_roach()])
        rch_OL = selector_supply([trn_OL, trn_roach])
        trn_roach_many = BTZSequence([rch_OL,rch_OL,rch_OL,rch_OL,rch_OL,rch_OL])
        trn_drn_many =  BTZSequence([drn_OL,drn_OL,drn_OL,drn_OL,drn_OL,drn_OL])
        
        sup_up = selector_supply([trn_OL, trn_roach_many])
        
        
        send_sweeps = BTZSequence([leaf_select_army(),leaf_attack_sweeps()])
        sweeps = selector_sweeps([nop, send_sweeps])
        
        attack_roach = BTZSequence([queen_upkeep,  selector_larva_to_roach([sup_up, send]), sweeps])
        
        gas_harv = BTZSequence([get_drone, leaf_extract_gas(),get_drone, leaf_extract_gas(),get_drone, leaf_extract_gas(),trn_drn_many])
        
        
        q_up_seq = BTZSequence([queen_upkeep, trn_roach_many,trn_roach_many])
        
        prep_roach = selector_count_gas_worker([gas_harv, q_up_seq])
        
        can_gas = leaf_build_extractor() #this may need redoing
        gas = BTZSequence([get_drone,can_gas, drn_OL])
       
        queen_gas = BTZSequence([trn_queen, drn_OL])
        gas_queen = BTZSequence([set_wp, selector_gas_queen([gas, gas, queen_gas,drn_OL]), drn_OL])
        rw_can = selector_can_build_roach_warren([leaf_build_roach_warren(),nop])
        rw_seq = BTZSequence([get_drone,rw_can])
    
        
        build_roach = selector_roach_warren_exist([selector_spawning_pool_exist([sp_seq, rw_seq]),  gas_queen])
        
        phase_roach = selector_roach_opening_phase([build_roach,prep_roach,attack_roach])
        
        
        
        decide_opening = selector_opening([phase_Qling,phase_roach])
       
        observe = decorator_step_obs([phase_roach])
        
        self.root = BTZRoot([observe])     
       
    
    
def main(unused_argv):
    agent1 = ZergAgent()
    agent2 = Zerg_Gas_Agent.ZergGasAgent() # sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)
    try:
        while True:# sc2_env.Agent(sc2_env.Race.zerg)
            with sc2_env.SC2Env(map_name="Catalyst", players=[sc2_env.Agent(sc2_env.Race.zerg), sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.medium)],
                agent_interface_format=features.AgentInterfaceFormat(feature_dimensions=features.Dimensions(screen=84, minimap=64),use_feature_units=True),
                      step_mul=16,
                      game_steps_per_episode=0,
                      visualize=False) as env:
                
                run_loop([agent1], env)
                    
                  
    except KeyboardInterrupt:
        pass
  
if __name__ == "__main__":
    app.run(main)
