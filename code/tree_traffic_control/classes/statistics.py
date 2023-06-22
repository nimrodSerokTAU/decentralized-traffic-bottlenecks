
class IterationStats:
    def __init__(self, iterations_count, output_path):
        self.iteration_entered_count = []
        self.iteration_arrived_count = []
        self.vehicles_inside_dict = {}
        self.prev_sec_list = []
        self.total_driving_time = 0
        self.total_duration_plus_before_insert = 0
        self.iterations_count = iterations_count + 1
        self.node_phases = []
        self.output_path = output_path

    def update_vehicles_inside(self, list_current_ids, sec_since_start, iteration):
        if iteration > len(self.iteration_entered_count) - 1:
            self.iteration_entered_count.append(0)
            self.iteration_arrived_count.append(0)
        for v_id in list_current_ids:
            if v_id not in self.vehicles_inside_dict:
                self.iteration_entered_count[iteration] += 1
                self.vehicles_inside_dict[v_id] = VehicleStats(v_id, sec_since_start, iteration)
        for v_id in self.prev_sec_list:
            if v_id not in list_current_ids:
                v_details = self.vehicles_inside_dict.pop(v_id, None)
                self.iteration_arrived_count[iteration] += 1
                self.total_driving_time += v_details.calc_time_inside(sec_since_start)

        self.prev_sec_list = list_current_ids

    def print_me_per_iteration(self):
        file_name = self.output_path + '/vehicles_stats.txt'
        source_file = open(file_name, 'w')
        for i in range(self.iterations_count):
            data = "{0:3d}, {1:5d}, {2:5d}, {3:5d}".format(i, self.iteration_entered_count[i], self.iteration_arrived_count[i],
                                                           sum(self.iteration_arrived_count[:i]))
            print(data, file=source_file)

        print('totals:', file=source_file)
        print('entered: {0}'.format(sum(self.iteration_entered_count)), file=source_file)
        print('arrived: {0}'.format(sum(self.iteration_arrived_count)), file=source_file)
        print('avg in-simulation duration: {0}'.format(self.total_driving_time / sum(self.iteration_arrived_count)), file=source_file)

    def fill_node_phases(self, nodes, nodes_keys):
        for iteration in range(self.iterations_count - 1):
            self.node_phases.append([])
            for node_key in nodes_keys:
                node = nodes[node_key]
                self.node_phases[iteration].append(node.phases_breakdown_per_iter[iteration])


class VehicleStats:
    def __init__(self, vehicle_id, sec_since_start, iteration):
        self.vehicle_id = vehicle_id
        self.sec_since_start: int = sec_since_start
        self.iteration = iteration
        self.time_inside = 0

    def calc_time_inside(self, current_sec_since_start):
        return current_sec_since_start - self.sec_since_start




