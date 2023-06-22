from config import MAX_DENSITY, ITERATION_TIME_MINUTES, M, L, MIN_VELOCITY
from enums import CostType


class Link:
    def __init__(self, link_id, edge_name, from_node_name, to_node_name, distance, lanes, free_flow_v, head_names):
        self.link_id = link_id
        self.from_node_name = from_node_name
        self.to_node_name = to_node_name
        self.distance_meters = distance
        self.lanes = lanes
        self.free_flow_v_km_h = free_flow_v * 3.6
        self.edge_name = edge_name
        self.speed_each_sec = []
        self.speeds_sec_sum = 0
        self.calc_iteration_speed = []
        self.is_loaded = False
        self.q_max_properties = None
        self.iteration_data = []
        self.links_names_to_me = []
        self.links_to_me = []
        self.links_from_me = []
        self.in_tree_fathers = {}
        self.is_lead_to_tl = None
        self.head_names = head_names
        self.cost_data_per_iter = []

    def join_links_to_me(self, links_connections, link_names):
        if self.edge_name in links_connections:
            for link_in_name in links_connections[self.edge_name].to_me:
                if link_in_name in link_names:
                    self.links_names_to_me.append(link_in_name)
                    self.links_to_me.append(link_names[link_in_name])
                elif link_in_name in links_connections:
                    for rear_link_name in links_connections[link_in_name].to_me:
                        if rear_link_name in link_names:
                            self.links_names_to_me.append(rear_link_name)
                            self.links_to_me.append(link_names[rear_link_name])

    def join_links_from_me(self, links_connections, link_names):
        if self.edge_name in links_connections:
            for link_out_name in links_connections[self.edge_name].from_me:
                if link_out_name in link_names:
                    self.links_from_me.append(link_names[link_out_name])
                elif link_out_name in links_connections:
                    for rear_link_name in links_connections[link_out_name].from_me:
                        if rear_link_name in link_names:
                            self.links_from_me.append(link_names[rear_link_name])

    def fill_my_speed(self, speed_m_s):
        speed_km_h = speed_m_s * 3.6
        self.speed_each_sec.append(speed_km_h)
        self.speeds_sec_sum += speed_km_h

    def add_speed_to_calculation(self, iteration):
        self.calc_iteration_speed.append(round(self.speeds_sec_sum / len(self.speed_each_sec)))
        self.speeds_sec_sum = 0
        self.speed_each_sec = []

    def calc_max_properties(self):
        q_max = 0
        q_max_u = -1
        for k in range(MAX_DENSITY):
            u = self.calc_u_by_k(k)
            q = u * k * self.lanes
            if q > q_max:
                q_max = q
                q_max_u = u

        self.q_max_properties = QmaxProperties(q_max_u, q_max, self.calc_dist_in_iter_time(q_max_u))

    def calc_u_by_k(self, current_density):  # test for k=50, uf=90, u=42.73
        return max(round(self.free_flow_v_km_h * ((1 - (current_density / MAX_DENSITY) ** (L - 1)) ** (1 / (1 - M)))), MIN_VELOCITY)

    def calc_k_by_u(self, current_speed_km_h):  # test for k=50, uf=90, u=42.73
        return max(round(MAX_DENSITY * ((max(1 - (current_speed_km_h / self.free_flow_v_km_h), 0) ** (1 - M)) ** (1 / (L - 1)))), 0)

    def calc_dist_in_iter_time(self, velocity):
        return min(round(velocity * 1000 / (60 / ITERATION_TIME_MINUTES)), self.distance_meters)  # meters

    def calc_my_iteration_data(self, iteration, loaded_per_iter):  # q = uk
        current_speed = max(self.calc_iteration_speed[-1], MIN_VELOCITY)
        current_density = self.calc_k_by_u(current_speed)
        current_flow_per_lane_per_hour = current_speed * current_density
        current_flow_per_iter = current_flow_per_lane_per_hour * self.lanes / (60 / ITERATION_TIME_MINUTES)
        self.is_loaded = current_speed < self.q_max_properties.q_max_u

        iteration_distance_meters = self.calc_dist_in_iter_time(current_speed)  # meters;
        time_loss_m = 0
        current_cost_minutes = 0

        if self.is_loaded:
            loaded_per_iter[-1].append(self.link_id)
            opt_time_h = self.q_max_properties.q_max_dist_in_iter_time / 1000 / self.q_max_properties.q_max_u
            actual_time_h = iteration_distance_meters / 1000 / current_speed
            time_loss_m = (actual_time_h - opt_time_h) * 60
            current_cost_minutes = round(current_flow_per_iter * time_loss_m)  # in minutes. per iteration;

        res = IterationData(self.link_id, iteration, current_speed, time_loss_m, current_cost_minutes, current_flow_per_iter, self.is_loaded)
        self.iteration_data.append(res)

    def find_potential_link_son_for_tree(self):
        if self.is_loaded:
            return self.links_to_me
        return None

    def calc_is_lead_to_tl(self, is_lead_to_tl):
        self.is_lead_to_tl = is_lead_to_tl

    def calc_heads_costs(self, heads_costs, current_trees, cost_type, all_heads):
        if self.link_id in current_trees.all_trees_per_iteration:
            link_cost = current_trees.all_trees_per_iteration[self.link_id].get_cost_by_type(cost_type)
            heads_vehicles_count_sum = 0
            for head_name in self.head_names:
                heads_vehicles_count_sum += all_heads[head_name].iterations_vehicle_count[-1]
            for head_name in self.head_names:
                heads_costs[head_name] = all_heads[head_name].iterations_vehicle_count[-1] / heads_vehicles_count_sum * link_cost

    def fill_my_cost_and_weight(self, iteration, cost_type: CostType):
        current_weight = 1 / len(self.in_tree_fathers[iteration]) if iteration in self.in_tree_fathers else 0
        current_weight = round(current_weight, 2) if cost_type in [CostType.TREE_CUMULATIVE_DIVIDED.name, CostType.TREE_CURRENT_DIVIDED.name,
                                                                   CostType.TREE_CUMULATIVE_DIVIDED_LTD.name] else 1
        current_cost = self.iteration_data[iteration].current_cost_minutes
        self.cost_data_per_iter.append(LinkIterationCost(iteration, current_cost, current_weight))


class IterationData:
    def __init__(self, link_id, iteration, current_speed, time_loss, current_cost_minutes, current_flow_per_iter, is_loaded):
        self.link_id = link_id
        self.iteration = iteration
        self.current_speed = current_speed
        self.time_loss = time_loss
        self.current_cost_minutes = current_cost_minutes
        self.current_flow_per_iter = current_flow_per_iter
        self.is_loaded = is_loaded


class QmaxProperties:
    def __init__(self, q_max_u, q_max, q_max_dist_in_iter_time):
        self.q_max = q_max
        self.q_max_u = q_max_u
        self.q_max_dist_in_iter_time = q_max_dist_in_iter_time  # meters;


class LinkIterationCost:
    def __init__(self, iteration, current_cost, current_weight):
        self.iteration = iteration
        self.current_cost = current_cost
        self.current_weight = current_weight
        self.current_cost_for_tree = round(current_weight * current_cost, 2)

