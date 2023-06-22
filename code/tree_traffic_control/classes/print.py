
class PrintData:
    def __init__(self, links, nodes, tl_node_ids, output_path):
        self.iterations = None
        self.links = links
        self.nodes = nodes
        self.tl_node_ids = tl_node_ids
        self.vehicle_total_time = None
        self.ended_vehicles_count = None
        self.started_vehicles_count = None
        self.costs = []
        self.driving_time_distribution = open(output_path + '/driving_time_distribution.txt', 'w')
        self.tree_cost_distribution = open(output_path + '/tree_cost_distribution.txt', 'w')

    def update_end_data(self, iterations, vehicle_total_time, ended_vehicles_count, started_vehicles_count):
        self.iterations = iterations
        self.vehicle_total_time = vehicle_total_time
        self.ended_vehicles_count = ended_vehicles_count
        self.started_vehicles_count = started_vehicles_count

    def vehicles_stats_print_summary(self):
        return {'ended_vehicles_count': self.ended_vehicles_count, 'started_vehicles_count': self.started_vehicles_count,
                'time per v': round(self.vehicle_total_time / self.ended_vehicles_count)}

    def print_vehicles_stats(self):
        print('total_time: ' + str(self.vehicle_total_time))
        print('ended_vehicles_count: ' + str(self.ended_vehicles_count))
        print('started_vehicles_count: ' + str(self.started_vehicles_count))
        print('time per v: ' + str(round(self.vehicle_total_time / self.ended_vehicles_count)))

    def print_driving_time_distribution(self, driving_time_seconds):
        for driving_time in driving_time_seconds:
            row = str(driving_time) + ','
            print(row, file=self.driving_time_distribution)

    def add_iter_tree_costs(self, single_iter_trees_costs):
        self.costs += single_iter_trees_costs

    def print_trees_costs(self):
        for tree_cost in self.costs:
            row = str(tree_cost.iteration) + ',' + str(tree_cost.cost) + ','
            print(row, file=self.tree_cost_distribution)
