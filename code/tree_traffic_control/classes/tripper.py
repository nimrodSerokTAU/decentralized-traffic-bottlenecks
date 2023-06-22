from __future__ import absolute_import
from __future__ import print_function

from typing import List

import json
import random
MEASUREMENT_DURATION = 15
COUNT_FACTOR = 1


def find_index_of_bin(bin_ends, rand):
    for inx, th in enumerate(bin_ends):
        if rand < th:
            return inx
    if rand == 0:
        return 0
    return len(bin_ends) - 1


class Trip:
    def __init__(self, from_road_name, to_road_name):
        self.orig = from_road_name
        self.dest = to_road_name
        self.init_time_sec = 0

    def set_init_time(self, measurement_iteration: int, minute_iter: int):
        self.init_time_sec = (measurement_iteration * MEASUREMENT_DURATION + minute_iter) * 60 + random.randint(0, 60)

    def get_my_print(self, inx: int):
        return '''<trip id="veh{}" type="veh_passenger" depart="{}" departLane="best" from ="{}" to="{}" />''' \
            .format(inx, self.init_time_sec, self.orig, self.dest)


class Entrance:
    def __init__(self, name, in_per_minute, allowed):
        self.name = name
        self.in_per_minute = in_per_minute
        self.allowed = allowed


class Exit:
    def __init__(self, name, out_per_minute):
        self.name = name
        self.out_per_minute = out_per_minute


class OneMinute:
    def __init__(self, measurement_iteration: int, roads_in_dict, dest_map_to_allowed_origins, minute_iter: int, exists_counters,
                 origins_list: List[str], measurement_iter_entrance_stats, measurement_iter_exit_stats):
        self.potential_trips: List[Trip] = []
        self.origins_list = origins_list
        self.destinations_bins_count = exists_counters
        self.roads_in_dict = roads_in_dict
        self.dest_map_to_allowed_origins = dest_map_to_allowed_origins
        self.measurement_iteration = measurement_iteration
        self.minute_iter = minute_iter
        self.minute_entrance_stats = measurement_iter_entrance_stats
        self.minute_exit_stats = measurement_iter_exit_stats

    def calculate_my_trips(self):
        random.shuffle(self.origins_list)
        for inx, origin in enumerate(self.origins_list):
            self.potential_trips.append(self.create_potential_trip(origin, inx))
        random.shuffle(self.potential_trips)
        for trip in self.potential_trips:
            trip.set_init_time(self.measurement_iteration, self.minute_iter)
        self.potential_trips.sort(key=lambda x: x.init_time_sec)
        return self.potential_trips

    def create_potential_trip(self, origin_name, origin_inx):
        bins_sum = 0
        bin_ends = [0]
        bin_names = []
        for dest_name in self.roads_in_dict[origin_name].allowed:
            if dest_name in self.destinations_bins_count:
                bin_size = self.destinations_bins_count[dest_name]
                bin_ends.append(bin_ends[-1] + bin_size)
                bins_sum += bin_size
                bin_names.append(dest_name)
        if bins_sum > 0:
            rand = random.randint(0, bins_sum)
            bin_index = find_index_of_bin(bin_ends[1:], rand)
            destination_name = bin_names[bin_index]
            new_trip = Trip(origin_name, destination_name)
            self.destinations_bins_count[destination_name] -= 1
            if self.destinations_bins_count[destination_name] == 0:
                self.destinations_bins_count.pop(destination_name)
            return new_trip
        else:  # if you reach a dead-end find the first trip which starts from a different origin and its dest is allowed for this origin.
            relevant_origins_to_switch_set = set()
            for dest_key in self.destinations_bins_count.keys():
                relevant_origins_to_switch_set.update(self.dest_map_to_allowed_origins[dest_key])
            for trip in self.potential_trips:
                if trip.dest in self.roads_in_dict[origin_name].allowed and trip.orig in relevant_origins_to_switch_set:
                    new_trip = Trip(origin_name, trip.dest)
                    potential_dest_to_replace = list(set(self.destinations_bins_count).intersection(self.roads_in_dict[trip.orig].allowed))
                    random.shuffle(potential_dest_to_replace)
                    trip.dest = potential_dest_to_replace[0]
                    self.destinations_bins_count[trip.dest] -= 1
                    if self.destinations_bins_count[trip.dest] == 0:
                        self.destinations_bins_count.pop(trip.dest)
                    return new_trip
            return None

    def add_trip_to_iter_stats(self, trip: Trip):
        self.minute_entrance_stats['drivers_count'] += 1
        self.minute_exit_stats['drivers_count'] += 1
        self.minute_entrance_stats[trip.orig] += 1
        self.minute_exit_stats[trip.dest] += 1


class Tripper:
    def __init__(self, file_path, is_random: bool):
        self.entrances_dict = {}
        self.exists = []
        self.dest_map_to_allowed_origins = {}
        self.measurement_iterations_count = None
        self.entrance_iter_stats = []
        self.exit_iter_stats = []
        self.file_path = file_path
        self.fill_me(file_path + 'trips-distribution.json')
        self.create_trips(file_path + 'vehicles.trips.xml', is_random)
        self.print_iters_stats()

    def fill_me(self, file_path):
        f = open(file_path)
        data = json.load(f)
        for r in data['roads_in']:
            entrance = Entrance(r['name'], r['in_per_minute'], r['allowed'])
            self.entrances_dict[entrance.name] = entrance
            for dest_name in entrance.allowed:
                if dest_name not in self.dest_map_to_allowed_origins:
                    self.dest_map_to_allowed_origins[dest_name] = set()
                self.dest_map_to_allowed_origins[dest_name].add(entrance.name)
        self.measurement_iterations_count = len(list(self.entrances_dict.values())[0].in_per_minute)
        for e in data['roads_out']:
            self.exists.append(Exit(e['name'], e['out_per_minute']))

    def create_trips(self, file_path_out, is_random):
        source_file = open(file_path_out, 'w')
        print('''<?xml version="1.0" encoding="UTF-8"?>
        <routes>
            <vType id="veh_passenger" vClass="passenger" lcStrategic="0.1"/>''', file=source_file)
        veh_id = 0
        for measurement_iteration in range(self.measurement_iterations_count):
            origins_list: List[str] = []
            measurement_iter_entrance_stats = {'drivers_count': 0}
            measurement_iter_exit_stats = {'drivers_count': 0}
            if is_random:
                entrance_keys_list = list(self.entrances_dict.keys())
                for minute_iter in range(MEASUREMENT_DURATION):
                    iter_trips = []
                    vehicles_count = 0
                    for entrance_data in self.entrances_dict.values():
                        vehicles_count += int(entrance_data.in_per_minute[measurement_iteration] * COUNT_FACTOR)
                    for v_inx in range(vehicles_count):
                        entrance_inx = random.randint(0, len(entrance_keys_list) - 1)
                        entrance_key = entrance_keys_list[entrance_inx]
                        exist_key_inx = random.randint(0, len(self.entrances_dict[entrance_key].allowed) - 1)
                        exit_key = self.entrances_dict[entrance_key].allowed[exist_key_inx]
                        trip = Trip(entrance_key, exit_key)
                        trip.set_init_time(measurement_iteration, minute_iter)
                        iter_trips.append(trip)
                        iter_trips.sort(key=lambda x: x.init_time_sec)
                    for trip in iter_trips:
                        print(trip.get_my_print(veh_id), file=source_file)
                        veh_id += 1
            else:
                for entrance_data in self.entrances_dict.values():
                    measurement_iter_entrance_stats[entrance_data.name] = 0
                    for inx in range(int(entrance_data.in_per_minute[measurement_iteration] * COUNT_FACTOR)):
                        origins_list.append(entrance_data.name)
                cars_count = len(origins_list)
                exists_counters = {}
                exists_sum = 0
                for exist_data in self.exists:
                    exists_sum += exist_data.out_per_minute[measurement_iteration]
                    exists_counters[exist_data.name] = exist_data.out_per_minute[measurement_iteration]
                    measurement_iter_exit_stats[exist_data.name] = 0
                for exist_data_key in exists_counters.keys():
                    exists_counters[exist_data_key] = int(exists_counters[exist_data_key] / exists_sum * cars_count) + 1
                for minute_iter in range(MEASUREMENT_DURATION):
                    minute_data = OneMinute(measurement_iteration, self.entrances_dict, self.dest_map_to_allowed_origins, minute_iter,
                                            exists_counters.copy(), origins_list, measurement_iter_entrance_stats.copy(),
                                            measurement_iter_exit_stats.copy())
                    iter_trips: List[Trip] = minute_data.calculate_my_trips()
                    for trip in iter_trips:
                        print(trip.get_my_print(veh_id), file=source_file)
                        minute_data.add_trip_to_iter_stats(trip)
                        veh_id += 1
                    self.entrance_iter_stats.append(minute_data.minute_entrance_stats)
                    self.exit_iter_stats.append(minute_data.minute_exit_stats)

        print('''</routes>''', file=source_file)
        source_file.close()

    def print_iters_stats(self):
        file_name = self.file_path + 'entrances_calc.txt'
        source_file = open(file_name, 'w')
        for iter_stats in self.entrance_iter_stats:
            print(iter_stats, file=source_file)
        file_name = self.file_path + 'exists_calc.txt'
        source_file = open(file_name, 'w')
        for iter_stats in self.exit_iter_stats:
            print(iter_stats, file=source_file)


Tripper('../simulationFolder/', False)

