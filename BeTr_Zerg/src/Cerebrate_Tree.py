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
        
        """ Misc Nodes """
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

        drn_OL =  selector_supply([trn_OL, trn_drn])
        
        set_wp = selector_is_wapyoint_set([nop, BTZSequence([leaf_select_unit_random(units.Zerg.Hatchery), leaf_simple_waypoint_close()])])
        
        trn_drn_many =  BTZSequence([drn_OL,drn_OL,drn_OL,drn_OL,drn_OL,drn_OL])
        
        can_gas = leaf_build_extractor() #this may need redoing
        gas = BTZSequence([get_drone,can_gas, drn_OL])
        
        queen_gas = BTZSequence([queen_upkeep, drn_OL])
        gas_queen = BTZSequence([set_wp, selector_gas_queen([gas, gas, queen_gas, nop])])
        
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
        """### OPENING ###"""
        
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
    
        b_r_s = BTZSequence([selector_spawning_pool_exist([sp_seq, gas_queen]), selector_roach_warren_exist([rw_seq, gas_queen])])
        
        build_roach = b_r_s
        
        ROACH_opening = selector_roach_opening_phase([build_roach, prep_roach,nop])
        
        
        
    
        
        decide_opening = selector_opening([LING_opening,ROACH_opening])
        """ ^^^OPENING^^^ """
        
        
        """###   BUILD   ###"""
        
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
        
        """ UPGRADES """
        
        start_mb_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZerglingMetabolicBoost_quick("now"), actions.FUNCTIONS.Research_ZerglingMetabolicBoost_quick.id, "metabolic_boost")
        can_mb_u = selector_can_uprade([start_mb_u,leaf_select_unit_random(units.Zerg.SpawningPool)], actions.FUNCTIONS.Research_ZerglingMetabolicBoost_quick.id)
        mb_u_sel_seq = selector_upgrade_tech_exists([can_mb_u,nop], units.Zerg.SpawningPool, "spawning_pool")
        
        start_ma_u = leaf_start_upgrade(actions.FUNCTIONS.Research_MuscularAugments_quick("now"), actions.FUNCTIONS.Research_ZerglingMetabolicBoost_quick.id, "muscular_augments")
        can_ma_u = selector_can_uprade([start_ma_u,leaf_select_unit_random(units.Zerg.HydraliskDen)], actions.FUNCTIONS.Research_MuscularAugments_quick.id)
        ma_u_sel_seq = selector_upgrade_tech_exists([can_ma_u,nop], units.Zerg.HydraliskDen, "hydralisk_den")
        
        start_gs_u = leaf_start_upgrade(actions.FUNCTIONS.Research_GroovedSpines_quick("now"),actions.FUNCTIONS.Research_MuscularAugments_quick.id, "grooved_spines")
        can_gs_u = selector_can_uprade([start_gs_u,leaf_select_unit_random(units.Zerg.HydraliskDen)], actions.FUNCTIONS.Research_GroovedSpines_quick.id)
        gs_u_sel_seq = selector_upgrade_tech_exists([can_gs_u,nop], units.Zerg.HydraliskDen, "hydralisk_den")
        
        start_ga_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZergGroundArmor_quick("now"),actions.FUNCTIONS.Research_ZergGroundArmor_quick.id, "ground_armor")
        can_ga_u = selector_can_uprade([start_ga_u,leaf_select_unit_random(units.Zerg.EvolutionChamber)], actions.FUNCTIONS.Research_ZergGroundArmor_quick.id)
        ga_u_sel_seq = selector_upgrade_tech_exists([can_ga_u,nop], units.Zerg.EvolutionChamber, "evolution_chamber")
        
        start_gr_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZergMissileWeapons_quick("now"),actions.FUNCTIONS.Research_ZergMissileWeapons_quick.id, "ground_ranged")
        can_gr_u = selector_can_uprade([start_gr_u,leaf_select_unit_random(units.Zerg.EvolutionChamber)], actions.FUNCTIONS.Research_ZergMissileWeapons_quick.id)
        gr_u_sel_seq = selector_upgrade_tech_exists([can_gr_u,nop], units.Zerg.EvolutionChamber, "evolution_chamber")
        
        start_gm_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZergMeleeWeapons_quick("now"),actions.FUNCTIONS.Research_ZergMeleeWeapons_quick.id, "ground_melee")
        can_gm_u = selector_can_uprade([start_gm_u,leaf_select_unit_random(units.Zerg.EvolutionChamber)], actions.FUNCTIONS.Research_ZergMeleeWeapons_quick.id)
        gm_u_sel_seq = selector_upgrade_tech_exists([can_gm_u,nop], units.Zerg.EvolutionChamber, "evolution_chamber")
        
        start_aa_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZergFlyerArmor_quick("now"),actions.FUNCTIONS.Research_ZergFlyerArmor_quick.id, "air_armor")
        can_aa_u = selector_can_uprade([start_aa_u,leaf_select_unit_random(units.Zerg.Spire)], actions.FUNCTIONS.Research_ZergFlyerArmor_quick.id)
        aa_u_sel_seq = selector_upgrade_tech_exists([can_aa_u,nop], units.Zerg.Spire, "spire")
        
        start_ar_u = leaf_start_upgrade(actions.FUNCTIONS.Research_ZergFlyerAttack_quick("now"),actions.FUNCTIONS.Research_ZergFlyerAttack_quick.id, "air_ranged")
        can_ar_u = selector_can_uprade([start_ar_u,leaf_select_unit_random(units.Zerg.Spire)], actions.FUNCTIONS.Research_ZergFlyerAttack_quick.id)
        ar_u_sel_seq = selector_upgrade_tech_exists([can_ar_u,nop], units.Zerg.Spire, "spire")
        
        
        """ PRODUCTION """
        
        trn_muta = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_mutalisk()])
        muta_OL = selector_supply([trn_OL, trn_muta])
        
        trn_hydra = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_hydralisk()])
        hydra_OL = selector_supply([trn_OL, trn_hydra])
        
        trn_ruptor = BTZSequence([leaf_select_unit_all(units.Zerg.Larva),leaf_train_corruptor()])
        ruptor_OL = selector_supply([trn_OL, trn_ruptor])
        
        
        ##print_army = 
        
        """ LING_MUTA """
        lm_production = BTZSequence([queen_upkeep, selector_fake_production_ratio_controller([ling_OL,muta_OL], "zergling", "mutalisk", 2)])
        lm_upgrades = selector_upgrade_progression_LM([mb_u_sel_seq, ga_u_sel_seq, aa_u_sel_seq, gm_u_sel_seq, ar_u_sel_seq, nop])
        lm_tech = selector_tech_progression_LM([sp_make,evo_make,lair_make,spire_make,decorator_tech_check([nop])])
        LING_MUTA = selector_build_progression([lm_tech,lm_upgrades,lm_production])
        
        
        """ ROACH_HYDRA """
        rh_production = BTZSequence([queen_upkeep,selector_fake_production_ratio_controller([rch_OL,hydra_OL], "roach", "hydralisk", 1)])
        rh_upgrades = selector_upgrade_progression_RH([ma_u_sel_seq, gs_u_sel_seq,ga_u_sel_seq,gr_u_sel_seq,nop])
        rh_tech = selector_tech_progression_RH([sp_make, rw_make, lair_make, evo_make, hd_make, decorator_tech_check([nop])])
        ROACH_HYDRA = selector_build_progression([rh_tech,rh_upgrades,rh_production])
        
        """ MUTA_RUPTOR """        
        mr_production = BTZSequence([queen_upkeep,selector_fake_production_ratio_controller([muta_OL,ruptor_OL], "mutalisk", "corruptor", .5)])
        mr_upgrades = selector_upgrade_progression_MR([ar_u_sel_seq,aa_u_sel_seq,nop])
        mr_tech  = selector_tech_progression_MR([sp_make, lair_make, spire_make, decorator_tech_check([nop])])
        MUTA_RUPTOR = selector_build_progression([mr_tech,mr_upgrades,mr_production])
        
        decide_build = selector_build_decision([LING_MUTA ,ROACH_HYDRA, MUTA_RUPTOR])
        
        """ ^^^BUILD^^^ """
        
        """###   RECON   ###"""
        
        
        noop = leaf_action_noop()

        base_cam = leaf_move_cam_to_base()
        select_scout_unit = leaf_select_unit_for_scouting()
        set_scout_cg = leaf_set_scouting_control_group()
        
        recall_scout = leaf_recall_scout_control_group()
        scout_cam = leaf_move_cam_to_scout()
        scouting_coords = BTZSequence([leaf_send_scout(coords=(x,y)) for (x,y) in [(10,10), (20,20), (30,30), (40,40), (50,50), (60,60)]])
        
        get_set_send_scouts = BTZSequence([select_scout_unit, set_scout_cg, scouting_coords])
        
        any_units_for_scouts = selector_any_scouts([get_set_send_scouts, noop])
        
        scouting_sequence = BTZSequence([base_cam, any_units_for_scouts])
        get_info = BTZSequence([recall_scout, scout_cam])
        
        any_scouts = selector_any_units_in_scouting_cg([scouting_sequence, get_info])
        
        get_enemy_status = decorator_get_enemy_information([any_scouts])
        
        
        #observe = decorator_step_obs([get_enemy_status])
        
        #self.root = BTZRoot([observe])

        
        """ ^^^RECON^^^ """
        
        
        """###   OFFENSE   ###"""
        
        attack = leaf_army_attack()
        move = leaf_army_move()
        get_army = leaf_select_army()
        cam_army = leaf_move_cam_to_army()
        
        nop = leaf_action_noop()
        
        warlord_nn = Warlord_NN([attack, move, nop])
        offence_tree = BTZSequence([get_army, cam_army, warlord_nn])
        
        
        
        """ ^^^OFFENSE^^^ """
        
        aspect_opening =  selector_cam_new_aspect([aspect_opening_subtree([decide_opening]), base_cam])
        aspect_build = selector_cam_new_aspect([aspect_build_subtree([decide_build]), base_cam])
        aspect_recon = aspect_recon_subtree([get_enemy_status])
        aspect_offense = aspect_recon_subtree([nop])
       
        king = selector_dummmy_king([ aspect_opening ,aspect_build,aspect_recon])
        
        observe = decorator_step_obs([decorator_upgrade_timer([king])])
        
        
        return BTZRoot([observe])     
       
 