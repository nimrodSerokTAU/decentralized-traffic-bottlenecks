from math import ceil

import traci
import random

from classes.phase import Phase
from config import MIN_PHASE_TIME
from enums import AlgoType
from classes.algo_config import CostToStepSize


def define_tl_program(j_key, inx, duration):
    traci.trafficlight.setPhase(j_key, inx)
    traci.trafficlight.setPhaseDuration(j_key, duration)


class JunctionNode:
    def __init__(self, node_id, node_name, links_in, links_out, is_traffic_light, tl_name, steps):
        self.node_id = node_id
        self.links_from_me = links_out
        self.links_to_me = links_in
        self.is_traffic_light = is_traffic_light
        self.name = node_name
        self.phases = []
        self.tl = tl_name
        self.min_phase_time = MIN_PHASE_TIME
        self.phase_key_per_sec = [None] * steps
        self.phases_breakdown_per_iter = []

    def add_my_phases(self, junctions_dict, link_names, heads_to_tails, all_heads):
        for inx, ph in enumerate(junctions_dict[self.name]["phases"]):
            phase_links = set()
            for head_name in ph['heads']:
                l_name = heads_to_tails[head_name]
                phase_links.add(link_names[l_name])
                all_heads[head_name].add_me_to_phase()
            self.phases.append(Phase(inx, ph['duration'], ph['heads'], phase_links))

    def calc_phases_cost(self, all_heads, heads_costs, iteration):
        for phase in self.phases:
            phase.calc_my_cost(all_heads, heads_costs, iteration)

    def calc_wanted_program(self, seconds_in_cycle, current_trees, cost_type, all_links, all_heads, iteration, algo_type):
        heads_costs = {}
        for link_id in self.links_to_me:
            all_links[link_id].calc_heads_costs(heads_costs, current_trees, cost_type, all_heads)
        self.calc_phases_cost(all_heads, heads_costs, iteration)
        sum_cost = sum(phase.cost for phase in self.phases)
        if algo_type == AlgoType.NAIVE.name:
            time_to_play_with = seconds_in_cycle - len(self.phases) * self.min_phase_time
            for phase_inx, phase in enumerate(self.phases):
                phase.define_duration(round(phase.cost / sum_cost * time_to_play_with + self.min_phase_time), iteration)
        elif algo_type == AlgoType.BABY_STEPS.name:
            cts = CostToStepSize()
            duration_step = cts.calc_duration_step(sum_cost)
            time_to_play_with = 0
            for phase in self.phases:
                time_to_play_with += phase.duration - max(phase.duration - duration_step, self.min_phase_time)
            new_phases_duration = []
            for phase_inx, phase in enumerate(self.phases):
                new_phases_duration.append(min(round(phase.cost / max(sum_cost, 1) * time_to_play_with +
                                                     max(phase.duration - duration_step, self.min_phase_time)),
                                               phase.duration + duration_step))
            left_over = seconds_in_cycle - sum(new_phases_duration)
            left_oer_base = left_over // len(self.phases)
            left_over_extra_count = left_over - left_oer_base * len(self.phases)
            for phase_inx, phase in enumerate(self.phases):
                phase_left_over = left_oer_base
                if phase_inx < left_over_extra_count:
                    phase_left_over += 1
                phase.define_duration(new_phases_duration[phase_inx] + phase_left_over, iteration)
        elif algo_type == AlgoType.PLANNED or algo_type == AlgoType.RANDOM.name:
            for phase in self.phases:
                phase.define_duration(-1, iteration)
        elif algo_type == AlgoType.UNIFORM.name:
            dur = ceil(seconds_in_cycle / len(self.phases))
            for phase in self.phases:
                phase.define_duration(dur, iteration)

    def save_phase(self, sec):
        self.phase_key_per_sec[sec] = traci.trafficlight.getPhase(self.tl)

    def aggregate_phases_per_iter(self, iteration, seconds_in_cycle):
        data = self.phase_key_per_sec[iteration * seconds_in_cycle: (iteration + 1) * seconds_in_cycle:]
        phases_breakdown = {'switch_count': 0}
        prev_phase = data[0]
        for phase_key in data:
            if phase_key not in phases_breakdown:
                phases_breakdown[phase_key] = 0
            phases_breakdown[phase_key] += 1
            if phase_key != prev_phase:
                phases_breakdown['switch_count'] += 1
            prev_phase = phase_key
        self.phases_breakdown_per_iter.append(phases_breakdown)

    def update_traffic_light(self, inner_sec, algo_type):
        if algo_type == AlgoType.RANDOM.name:
            if inner_sec % MIN_PHASE_TIME == 0:
                phase_inx = random.randint(0, len(self.phases) - 1)
                define_tl_program(self.tl, phase_inx, MIN_PHASE_TIME)
            return
        secs_sum = 0
        for inx, phase in enumerate(self.phases):
            if inner_sec is secs_sum:
                define_tl_program(self.tl, inx, phase.duration)
                break
            secs_sum += phase.duration
