
class CostToStepSize:
    def __init__(self):
        self.sum_th = [10, 30, 100, 300, 1000, 10000000]
        self.step_size = [2, 4, 6, 10, 15, 20, 25]

    def calc_duration_step(self, sum_cost):
        for i, th in enumerate(self.sum_th):
            if sum_cost < th:
                return self.step_size[i]




