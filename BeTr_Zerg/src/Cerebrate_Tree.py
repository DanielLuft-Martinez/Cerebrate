from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random

from BeTr_Zerg import *
from nodes_BeTr_Zerg import *
from BeTr_Zerg import BTZSequence, BTZRoot


class CerebrateTree(object):
    
    
    name = ""
    root = BTZRoot([])
    
     

    def __init__(self, name):
       self.name = name        


    def build_tree(self):
        
        """ Queen Ling open """
        get_drone = selector_idle_workers([leaf_select_drone_random(), leaf_select_idle_worker()]);
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
        
        set_wp = BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery), leaf_simple_waypoint_close()])
        
        trn_drn_many =  BTZSequence([drn_OL,drn_OL,drn_OL,drn_OL,drn_OL,drn_OL])
        
        can_gas = leaf_build_extractor() #this may need redoing
        gas = BTZSequence([get_drone,can_gas, drn_OL])
        
        queen_gas = BTZSequence([trn_queen, drn_OL])
        gas_queen = BTZSequence([set_wp, selector_gas_queen([gas, gas, queen_gas, nop]), nop])
        
        drn_at_least = selector_worker_at_least([nop, trn_drn_many])

        gas_harv = BTZSequence([get_drone, leaf_extract_gas(),get_drone, leaf_extract_gas(),get_drone, leaf_extract_gas(), drn_at_least])

        ling_OL = selector_supply([trn_OL, trn_ling])
        trn_ling_many = BTZSequence([ling_OL,ling_OL,ling_OL,ling_OL,ling_OL,ling_OL])
        
        prep = selector_queen_upkeep([queen_upkeep,selector_supply([trn_OL,trn_ling])])
        
        launch = leaf_attack()
        
        send = BTZSequence([leaf_select_army(),launch])
        
        wave = selector_supply([trn_OL, selector_ling_attack_wave([selector_supply([trn_OL,trn_ling_all]),send])])
        
        # attack = selector_queen_upkeep([queen_upkeep,wave])
        
        # build = selector_spawning_pool_exist([sp_seq,trn_queen])
        
        # opener_Qling = selector_build_phase([build, prep, attack])
        
        
        ## OLD LING OPENING STUFF
        ##phase_ling = decorator_phase_queen_ling([opener_Qling])
        
        
        """  Ling open """
        
        
        q_up_seq_ling = BTZSequence([queen_upkeep, trn_ling_many,trn_ling_many, drn_at_least])
        
        prep_ling = selector_count_gas_worker([gas_harv, q_up_seq_ling])
        
        
        build_ling = selector_spawning_pool_exist([sp_seq, gas_queen])
        
        
        LING_opening = selector_zergling_opening_phase([build_ling, prep_ling, nop])
        
        """  Roach open """
        
        
        
        trn_roach = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_roach()])
        rch_OL = selector_supply([trn_OL, trn_roach])
        trn_roach_many = BTZSequence([rch_OL,rch_OL,rch_OL,rch_OL,rch_OL,rch_OL])
        
       
        
        ## OLD ATTACK SEQUENCE STUFF
        
        #sup_up = selector_supply([trn_OL, trn_roach_many])
        #send_sweeps = BTZSequence([leaf_select_army(),leaf_attack_sweeps()])
        #sweeps = selector_sweeps([nop, send_sweeps])
        ##attack_roach = BTZSequence([queen_upkeep,  selector_larva_to_roach([sup_up, send]), sweeps])
        q_up_seq_roach = BTZSequence([queen_upkeep, trn_roach_many,trn_roach_many, drn_at_least])
        
        
        
        prep_roach = selector_count_gas_worker([gas_harv, q_up_seq_roach])
        
        rw_can = selector_can_build_roach_warren([leaf_build_roach_warren(),nop])
        rw_seq = BTZSequence([get_drone,rw_can])
    
        
        build_roach = selector_roach_warren_exist([selector_spawning_pool_exist([sp_seq, rw_seq]),  gas_queen])
        
        ROACH_opening = selector_roach_opening_phase([build_roach, prep_roach,nop])
        
        
        
    
        """ OPENING """
        decide_opening = selector_opening([LING_opening,ROACH_opening])
        
        """ ^^^OPENING^^^ """
        
        
        """    BUILD    """
        
        """  TECH  """
        evo_can = selector_can_build_evolution_chamber([leaf_build_evolution_chamber(),nop])
        lair_can = selector_can_morph_lair([leaf_morph_lair(),nop])
        spire_can = selector_can_build_spire([leaf_build_spire(),nop])
        hd_can = selector_can_build_hydralisk_den([leaf_build_hydralisk_den(),nop])
        
        sp_make = sp_seq
        evo_make = BTZSequence([get_drone,evo_can])
        lair_make = BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery),lair_can])
        spire_make = BTZSequence([get_drone,spire_can])
        rw_make = rw_seq
        hd_make = BTZSequence([get_drone,hd_can])
        
        
        """ LING_MUTA """
        
        
        lm_tech = selector_tech_progression_LM([sp_make,evo_make,lair_make,spire_make,nop])
        LING_MUTA = selector_build_progression([lm_tech,nop,nop])
        
        
        """ ROACH_HYDRA """
        
        rh_tech = selector_tech_progression_RH([sp_make, rw_make, lair_make, evo_make, hd_make, nop])
        ROACH_HYDRA = selector_build_progression([rh_tech,nop,nop])
        
        """ MUTA_RUPTOR """
        mr_tech  = selector_tech_progression_MR([sp_make, lair_make, spire_make, nop])
        MUTA_RUPTOR = selector_build_progression([mr_tech,nop,nop])
        
        decide_build = selector_build_decision([LING_MUTA ,ROACH_HYDRA, MUTA_RUPTOR])
        
        """ ^^^BUILD^^^ """
        
        
        
        aspect_opening = selector_cam_new_aspect([decide_opening , leaf_cam_aspect()])
        aspect_build = selector_cam_new_aspect([decide_build , leaf_cam_aspect()])
        aspect_econ = selector_cam_new_aspect([nop, leaf_cam_aspect()])
       
        king = selector_dummmy_king([ aspect_opening ,aspect_build,aspect_econ])
        
        observe = decorator_step_obs([king])
        
        
        return BTZRoot([observe])     
       
 