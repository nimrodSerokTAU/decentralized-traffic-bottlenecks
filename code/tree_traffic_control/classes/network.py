from __future__ import absolute_import
from __future__ import print_function


import json


class Network:
    def __init__(self, file_path):
        self.junctions_dict = {}
        self.edges_list = {}
        self.fill_me(file_path)

    def fill_me(self, file_path):
        f = open(file_path)
        data = json.load(f)
        self.junctions_dict = data['junctions_dict']
        self.edges_list = data['edges_list']

    def calc_cycle_time(self):
        first_key = list(self.junctions_dict.keys())[0]
        phases = self.junctions_dict[first_key]["phases"]
        return sum(phase['duration'] for phase in phases)



