import traci

from classes.iterations_trees import IterationTrees
from classes.link import Link
from classes.node import JunctionNode
from classes.head import Head
from classes.vehicle import Vehicle
from config import VEHICLES_MAX_NUM
from utils import get_vehicle_inx


class Graph:
    def __init__(self, steps):
        self.all_links = []
        self.all_nodes = []
        self.link_names = {}
        self.node_names = {}
        self.tl_node_ids = []
        self.links_connections = {}
        self.heads_to_tails = {}
        self.all_heads_dict = {}
        self.loaded_per_iter = []
        self.all_vehicles: [Vehicle] = [None] * VEHICLES_MAX_NUM
        self.last_iter_vehicles = set()
        self.this_iter_vehicles = set()
        self.ended_vehicles_count = 0
        self.started_vehicles_count = 0
        self.vehicle_total_time = 0
        self.steps = steps
        self.driving_Time_seconds = []
        self.ended_ids_test = []

    def create_links_connections_and_heads(self, edges_list):
        for inx, e in enumerate(edges_list):
            this_link = Link(inx, e['id'], e['from_junction'], e['to_junction'], e['distance'], e['lanes'], e['f_speed'], e['heads'])
            self.all_links.append(this_link)
            self.link_names[this_link.edge_name] = this_link.link_id
            if e['to_junction'] not in self.node_names:
                self.node_names[e['to_junction']] = NodeLinks()
            self.node_names[e['to_junction']].add_link_in(this_link.link_id)
            if e['from_junction'] not in self.node_names:
                self.node_names[e['from_junction']] = NodeLinks()
            self.node_names[e['from_junction']].add_link_out(this_link.link_id)
            for to_link_name in e['to']:
                self.create_connection(this_link.edge_name, to_link_name)
            for head in e['heads']:
                self.heads_to_tails[head] = this_link.edge_name
                self.all_heads_dict[head] = Head(head)

    def create_nodes(self, junctions_dict):

        for n_name in list(self.node_names.keys()):
            if len(self.node_names[n_name].links_in) > 0 and len(self.node_names[n_name].links_out) > 0:
                is_traffic_light = True if n_name in junctions_dict else False
                tl_name = None if n_name not in junctions_dict else junctions_dict[n_name]["tl"]
                this_node = JunctionNode(len(self.all_nodes), n_name, self.node_names[n_name].links_in, self.node_names[n_name].links_out,
                                         is_traffic_light, tl_name, self.steps)
                if is_traffic_light:
                    self.tl_node_ids.append(this_node.node_id)
                    this_node.add_my_phases(junctions_dict, self.link_names, self.heads_to_tails, self.all_heads_dict)
                self.all_nodes.append(this_node)
                self.node_names[this_node.name] = this_node
            else:
                self.node_names.pop(n_name, None)

    def create_connection(self, from_name, to_name):
        if from_name not in self.links_connections:
            self.links_connections[from_name] = LinkConnections()
        if to_name not in self.links_connections[from_name].from_me:
            self.links_connections[from_name].add_link_name_from_me(to_name)
        if to_name not in self.links_connections:
            self.links_connections[to_name] = LinkConnections()
        if from_name not in self.links_connections[to_name].to_me:
            self.links_connections[to_name].add_link_name_to_me(from_name)

    def build(self, edges_list, junctions_dict):
        self.create_links_connections_and_heads(edges_list)
        self.create_nodes(junctions_dict)
        for link in self.all_links:
            link.join_links_to_me(self.links_connections, self.link_names)
            link.join_links_from_me(self.links_connections, self.link_names)
            link.calc_max_properties()
            link.calc_is_lead_to_tl(self.node_names[link.to_node_name].is_traffic_light if link.to_node_name in self.node_names else False)

    def sum_edges_list(self, iteration):
        for link in self.all_links:
            link.add_speed_to_calculation(iteration)
        for head in list(self.all_heads_dict.values()):
            head.add_count_to_calculation()

    def close_prev_vehicle_step(self, step: int):
        ended: [int] = list(self.last_iter_vehicles.difference(self.this_iter_vehicles))
        started: [int] = list(self.this_iter_vehicles.difference(self.last_iter_vehicles))
        for v_id in ended:
            vehicle: Vehicle = self.all_vehicles[v_id]
            v_time = vehicle.end_drive(step)
            self.ended_ids_test.append(v_id)
            self.ended_vehicles_count += 1
            self.vehicle_total_time += v_time
            self.driving_Time_seconds.append(v_time)
        for v_id in started:
            self.all_vehicles[v_id] = Vehicle(v_id, step)
            self.started_vehicles_count += 1
        self.last_iter_vehicles = self.this_iter_vehicles.copy()
        self.this_iter_vehicles = set()

    def fill_link_in_step(self):
        for link in self.all_links:
            speed_m_per_s = traci.edge.getLastStepMeanSpeed(link.edge_name)
            link.fill_my_speed(speed_m_per_s)

    def update_traffic_lights(self, step, seconds_in_cycle, algo_type):
        for node_id in self.tl_node_ids:
            self.all_nodes[node_id].update_traffic_light(step % seconds_in_cycle, algo_type)

    def add_vehicles_to_step(self):
        vehicle_ids = traci.vehicle.getIDList()
        for v in vehicle_ids:
            v_inx = get_vehicle_inx(v)
            self.this_iter_vehicles.add(v_inx)

    def get_traffic_lights_phases(self, step):
        for node_id in self.tl_node_ids:
            self.all_nodes[node_id].save_phase(step)

    def calc_nodes_statistics(self, ended_iteration, seconds_in_cycle):
        for node_id in self.tl_node_ids:
            self.all_nodes[node_id].aggregate_phases_per_iter(ended_iteration, seconds_in_cycle)

    def calc_wanted_programs(self, seconds_in_cycle, iteration_trees, iteration, cost_type, algo_type):
        for node_id in self.tl_node_ids:
            self.all_nodes[node_id].calc_wanted_program(seconds_in_cycle, iteration_trees[-1], cost_type, self.all_links, self.all_heads_dict,
                                                        iteration, algo_type)

    def calculate_iteration(self, iteration, iteration_trees, step, seconds_in_cycle, cost_type, algo_type):
        self.sum_edges_list(iteration)
        self.loaded_per_iter.append([])
        for link in self.all_links:
            link.calc_my_iteration_data(iteration, self.loaded_per_iter)
        this_iter_trees = IterationTrees(iteration, self.all_links, cost_type)
        iteration_trees.append(this_iter_trees)
        self.calc_wanted_programs(seconds_in_cycle, iteration_trees, iteration, cost_type, algo_type)
        return this_iter_trees.all_trees_costs

    def fill_head_iteration(self):
        for head in list(self.all_heads_dict.values()):
            vehicle_count = traci.edge.getLastStepVehicleNumber(head.name)
            head.fill_my_count(vehicle_count)


class LinkConnections:
    def __init__(self):
        self.from_me = []
        self.to_me = []

    def add_link_name_from_me(self, name):
        self.from_me.append(name)

    def add_link_name_to_me(self, name):
        self.to_me.append(name)


class NodeLinks:
    def __init__(self):
        self.links_out = []
        self.links_in = []

    def add_link_out(self, link_id):
        self.links_out.append(link_id)

    def add_link_in(self, link_id):
        self.links_in.append(link_id)
