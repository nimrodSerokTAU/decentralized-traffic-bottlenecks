
from config import IS_DIVIDE_COST


class Phase:
    def __init__(self, phase_id, duration, heads, links):
        self.phase_id = phase_id
        self.duration = duration
        self.heads = heads
        self.link_ids = links
        self.cost = 0

    def calc_my_cost(self, all_heads, heads_cost, iteration):
        self.cost = 0
        for head_name in self.heads:
            if head_name in heads_cost:
                if IS_DIVIDE_COST:
                    self.cost += heads_cost[head_name] / all_heads[head_name].phase_count
                else:
                    self.cost += heads_cost[head_name]

    def define_duration(self, duration, iteration):
        if duration > 0:
            self.duration = duration

