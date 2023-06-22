#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2022 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    runner.py
# @author  Lena Kalleske
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2009-03-26

from __future__ import absolute_import
from __future__ import print_function

import os
import sys

# we need to import python modules from the $SUMO_HOME/tools directory


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci  # noqa
from classes.graph import Graph
from classes.print import PrintData
from classes.network import Network
from classes.statistics import IterationStats
from utils import calc_iteration_from_step, is_calculation_time
from classes.run_config import RunConfig
from config import SIMULATION_TIME_SEC

_nogui = True


"""
Before running: 
1. Run tripper.py to create the rivers
2. Run net-builder.py to create the network input
3. Run the runner.py to run the simulation
"""


def calculation_time(graph, iteration, step, iteration_trees, seconds_in_cycle, run_config, print_data):
    ended_iteration = iteration - 1
    this_iter_trees_costs = graph.calculate_iteration(ended_iteration, iteration_trees, step, seconds_in_cycle,
                                                      run_config.cost_type, run_config.algo_type)
    graph.calc_nodes_statistics(ended_iteration, seconds_in_cycle)
    print_data.add_iter_tree_costs(this_iter_trees_costs)


def closing_step(graph, step, seconds_in_cycle, iteration_stats):
    graph.get_traffic_lights_phases(step)
    traci.simulationStep()
    graph.fill_link_in_step()
    graph.add_vehicles_to_step()
    graph.close_prev_vehicle_step(step)
    iteration = calc_iteration_from_step(step, seconds_in_cycle)
    iteration_stats.update_vehicles_inside(traci.vehicle.getIDList(), step, iteration)
    graph.fill_head_iteration()
    return iteration


def closing_simulation(graph, iteration, print_data, iteration_stats):
    print_data.update_end_data(iteration, graph.vehicle_total_time, graph.ended_vehicles_count, graph.started_vehicles_count)
    print_data.print_driving_time_distribution(graph.driving_Time_seconds)
    print_data.print_vehicles_stats()
    print_data.print_trees_costs()
    iteration_stats.fill_node_phases(graph.all_nodes, graph.tl_node_ids)
    iteration_stats.print_me_per_iteration()
    # iteration_stats.print_node_phases(graph.all_nodes, graph.tl_node_ids)
    traci.close()
    sys.stdout.flush()


def run(sumo_binary, path, output_path, input_network_file, run_config: RunConfig):
    sumocfg_path = path + "/simulation.sumocfg"
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumo_binary, "-c", sumocfg_path,
                 "--tripinfo-output", "tripinfo.xml",
                 "--statistic-output", "stats.xml", "--tripinfo-output.write-unfinished", "--duration-log.statistics"  # , "--no-internal-links"
                 ])
    """
        iteration 0 is 0-89 seconds (steps)
    """
    network_data = Network(input_network_file)
    iteration_trees = []
    """execute the TraCI control loop"""
    step = 0
    iteration = 0
    graph = Graph(SIMULATION_TIME_SEC)
    graph.build(network_data.edges_list, network_data.junctions_dict)
    seconds_in_cycle = network_data.calc_cycle_time()
    iteration_stats = IterationStats(SIMULATION_TIME_SEC // seconds_in_cycle, output_path)
    print_data = PrintData(graph.all_links, graph.all_nodes, graph.tl_node_ids, output_path)

    # iteration 0 is 0-89 seconds
    while traci.simulation.getMinExpectedNumber() > 0 and step < SIMULATION_TIME_SEC:
        if is_calculation_time(step, seconds_in_cycle):
            calculation_time(graph, iteration, step, iteration_trees, seconds_in_cycle, run_config, print_data)
        if not run_config.is_actuated:
            graph.update_traffic_lights(step, seconds_in_cycle, run_config.algo_type)
        iteration = closing_step(graph, step, seconds_in_cycle, iteration_stats)
        step += 1
    closing_simulation(graph, iteration, print_data, iteration_stats)
    return print_data.vehicles_stats_print_summary()
