
def is_calculation_time(step, seconds_in_cycle):
    return step > 0 and step % seconds_in_cycle == 0


def calc_iteration_from_step(step, seconds_in_cycle):
    return (step + 1) // seconds_in_cycle


def get_vehicle_inx(vehicle_id):
    return int(vehicle_id[3:])
