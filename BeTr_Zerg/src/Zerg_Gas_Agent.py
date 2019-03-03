from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random


class ZergGasAgent(base_agent.BaseAgent):


    def __init__(self):
        super(ZergGasAgent, self).__init__()
        
        
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
        
        sp_loc_x = 0
        sp_loc_y = 0
        
        gasX = []
        gasY = []
        
        super(ZergGasAgent, self).step(obs)
        
        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative == 
            features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()
            
            
            self.gas_harvesters = 0

            
          
            
            
            #for geyser in TYPE_GEYSER:
            #   gasY.append( ((obs.observation.feature_screen.unit_type == geyser ).nonzero()))
            
            gasY,gasX = ((obs.observation.feature_screen.unit_type == 343 ).nonzero())
             
                

            
            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 53)

                
            else:
                self.attack_coordinates = (12, 16)

        
        
        
        free_supply = (obs.observation.player.food_cap - obs.observation.player.food_used)
        
        
        zerglings = self.get_units_by_type(obs, units.Zerg.Zergling)
        if len(zerglings) > 7:
            if self.unit_type_is_selected(obs, units.Zerg.Zergling):
                    if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                        return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
        
        if len(zerglings) >  7:
            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.FUNCTIONS.select_army("select")
        
        
        spawning_pools = self.get_units_by_type(obs, units.Zerg.SpawningPool)
        if len(spawning_pools) == 0:               
            if self.unit_type_is_selected(obs, units.Zerg.Drone):
                    if self.can_do(obs, actions.FUNCTIONS.Build_SpawningPool_screen.id):
                        gasY,gasX = ((obs.observation.feature_screen.unit_type == 343 ).nonzero())
                        x = random.choice(gasX)
                        y = random.choice(gasY)
        
                        return actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))
            drones = self.get_units_by_type(obs, units.Zerg.Drone)
            if len(drones) > 0:
                drone = random.choice(drones)
                return actions.FUNCTIONS.select_point("select", (drone.x,drone.y))
            
            
        extracors = self.get_units_by_type(obs, units.Zerg.Extractor)
        obs.observation.feature_screen
        if len(extracors) == 0:               
            if self.unit_type_is_selected(obs, units.Zerg.Drone):
                    if self.can_do(obs, actions.FUNCTIONS.Build_Extractor_screen.id):
                        gasY,gasX = ((obs.observation.feature_screen.unit_type == 343 ).nonzero())
                        x = random.choice(gasX)
                        y = random.choice(gasY)
        
                        return actions.FUNCTIONS.Build_Extractor_screen("now", (x, y))
            drones = self.get_units_by_type(obs, units.Zerg.Drone)
            if len(drones) > 0:
                drone = random.choice(drones)
                return actions.FUNCTIONS.select_point("select", (drone.x,drone.y))
        
        
        GHY,GHX = ((obs.observation.feature_screen.unit_type == 88 ).nonzero())
        if(len(GHX) > 0 and self.gas_harvesters < 3):
            if self.unit_type_is_selected(obs, units.Zerg.Drone):
                if (self.can_do(obs, actions.FUNCTIONS.Harvest_Gather_screen.id)):
                    self.gas_harvesters = self.gas_harvesters + 1
                   # print(self.gas_harvesters )
                    return actions.FUNCTIONS.Harvest_Gather_screen("queued", (GHX.mean(), GHY.mean()))
                        
            drones = self.get_units_by_type(obs, units.Zerg.Drone)
            if len(drones) > 0:
                drone = random.choice(drones)
                return actions.FUNCTIONS.select_point("select", (drone.x,drone.y))
        #if(obser)                       
                   
               
               
               
           
        if self.unit_type_is_selected(obs, units.Zerg.Larva):
            if free_supply <= 2:
                if self.can_do(obs, actions.FUNCTIONS.Train_Overlord_quick.id):
                    return actions.FUNCTIONS.Train_Overlord_quick("now")
            
            drones = self.get_units_by_type(obs, units.Zerg.Drone)
            if self.can_do(obs, actions.FUNCTIONS.Train_Drone_quick.id):
                if len(drones) < 14:
                    return actions.FUNCTIONS.Train_Drone_quick("now")
            
            if len(zerglings) < 20:
                if self.can_do(obs, actions.FUNCTIONS.Train_Zergling_quick.id):
                    return actions.FUNCTIONS.Train_Zergling_quick("now")
        
        larvae = self.get_units_by_type(obs, units.Zerg.Larva)
        if len(larvae) > 0:
            larva = random.choice(larvae)
        
            return actions.FUNCTIONS.select_point("select_all_type", (larva.x, larva.y))
        

        
        return actions.FUNCTIONS.no_op()
    
    
def main(unused_argv):
    agent = ZergGasAgent()
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
