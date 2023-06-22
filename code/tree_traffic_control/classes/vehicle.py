class Vehicle:
    def __init__(self, vehicle_inx, step):
        self.vehicle_id: int = vehicle_inx
        self.start_step: int = step
        self.end_step = None
        self.time = 0

    def end_drive(self, step: int):
        self.end_step = step
        self.time = self.end_step - self.start_step
        return self.time

