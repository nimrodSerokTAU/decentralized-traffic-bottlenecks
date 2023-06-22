class Head:
    def __init__(self, name):
        self.name = name
        self.total_vehicle_per_iteration = 0
        self.iterations_vehicle_count = []
        self.phase_count = 0

    def add_me_to_phase(self):
        self.phase_count += 1

    def fill_my_count(self, vehicle_number):
        self.total_vehicle_per_iteration += vehicle_number

    def add_count_to_calculation(self):
        self.iterations_vehicle_count.append(self.total_vehicle_per_iteration)
        self.total_vehicle_per_iteration = 0


