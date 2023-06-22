from __future__ import absolute_import
from __future__ import print_function

import xmltodict


def calc_junction_id(via):
    split_str = via.split('_')
    connected = ''
    for t in split_str[0:-2]:
        connected += t + '_'
    return connected[1:len(connected) - 1]


class NetworkData:
    def __init__(self, file_path_in, file_path_out):
        self.junctions_dict = {}
        self.file_path_in = file_path_in
        self.file_path_out = file_path_out
        self.file_data = None
        self.connections_per_tl = {}
        self.all_connections = {}
        self.tls = {}
        self.edges = {}
        self.heads = {}
        self.read_file()
        self.print_me()

    def read_file(self):
        with open(self.file_path_in) as fd:
            self.file_data = xmltodict.parse(fd.read())
        for connection in self.file_data['net']['connection']:
            if '@via' in connection:
                junction_id = calc_junction_id(connection['@via'])
                if '@tl' in connection:
                    if connection['@tl'] not in self.connections_per_tl:
                        self.connections_per_tl[connection['@tl']] = TrafficLight(junction_id)
                    self.connections_per_tl[connection['@tl']].add_connection(Connection(connection['@from'], int(connection['@linkIndex'])))
                from_edge = connection['@from']
                if from_edge not in self.all_connections:
                    self.all_connections[from_edge] = set()
                connection_dest = connection['@to'].split('_T')[0]
                self.all_connections[from_edge].add(connection_dest)

        for tl in list(self.connections_per_tl.values()):
            tl.connections.sort(key=lambda x: x.link_index)

        for tlLogic in self.file_data['net']['tlLogic']:
            self.tls[tlLogic['@id']] = TrafficLightLogic(self.connections_per_tl[tlLogic['@id']].junction_id)
            for phase in tlLogic['phase']:
                p_data = Phase(phase['@duration'], phase['@state'])
                for inx, state in enumerate(phase['@state']):
                    if state == 'G':
                        p_data.add_head(self.connections_per_tl[tlLogic['@id']].connections[inx].head)
                self.tls[tlLogic['@id']].add_phase(p_data)
            tl_data = self.tls[tlLogic['@id']]
            if tl_data.junction_id not in self.junctions_dict:
                self.junctions_dict[tl_data.junction_id] = Junction(tl_data.junction_id)
            self.junctions_dict[tl_data.junction_id].add_tl_data(tlLogic['@id'], tl_data.phases)

        for edge in self.file_data['net']['edge']:
            if '@function' in edge:
                continue
            if '_T' in edge['@id']:
                continue
            is_head = True if '_H_' in edge['@id'] else False
            first_part = None
            if is_head:
                first_part = edge['@id'].split('_H_')[0]
            edge_id = first_part if is_head else edge['@id']
            if edge_id not in self.edges:
                self.edges[edge_id] = Edge()
            if is_head:
                self.edges[edge_id].set_head(edge['@id'], edge['@to'], self.all_connections[edge['@id']])
                self.heads[edge['@id']] = {'to_junction': edge['@to']}
            else:
                first_lane = edge['lane'][0] if '@id' not in edge['lane'] else edge['lane']
                self.edges[edge_id].set_body(edge_id, edge['@from'], edge['@to'], 1 if '@id' in edge['lane'] else len(edge['lane']),
                                             first_lane['@speed'], first_lane['@length'])
                if edge['@from'] not in self.junctions_dict:
                    self.junctions_dict[edge['@from']] = Junction(edge['@from'])
                self.junctions_dict[edge['@from']].add_edge(edge['@id'])

        for edge in list(self.edges.values()):
            edge.set_junction()

    def print_me(self):
        source_file = open(self.file_path_out, 'w')
        print('{"edges_list": [', file=source_file)
        for inx, edge in enumerate(list(self.edges.values())):
            edge_string = edge.print_edge()
            if inx == len(list(self.edges.keys())) - 1:
                edge_string = edge_string[:-1]
            print(edge_string, file=source_file)
        print('],', file=source_file)

        print('"junctions_dict": {', file=source_file)
        junctions_list = list(filter(lambda junction_data: junction_data.tl is not None, list(self.junctions_dict.values())))
        for inx, junction_obj in enumerate(junctions_list):
            junction_string = junction_obj.print_junction()
            if inx == len(junctions_list) - 1:
                junction_string = junction_string[:-1]
            print(junction_string, file=source_file)
        print('}}', file=source_file)


class TrafficLight:
    def __init__(self, junction_id):
        self.connections = []
        self.junction_id = junction_id

    def add_connection(self, connection):
        self.connections.append(connection)


class TrafficLightLogic:
    def __init__(self, junction_id):
        self.phases = []
        self.junction_id = junction_id

    def add_phase(self, phase):
        self.phases.append(phase)


class Connection:
    def __init__(self, head, link_index):
        self.head = head
        self.link_index = link_index


class Edge:
    def __init__(self):
        self.is_head = None
        self.heads = []
        self.to = set()
        self.to_junction = None
        self.edge_id = None
        self.from_junction = None
        self.to_virtual_junction = None
        self.lanes = 0
        self.f_speed = 0
        self.distance = 0

    def set_head(self, head, to_junction, connections):
        self.is_head = True
        self.heads.append(head)
        self.to_junction = to_junction
        self.to = self.to.union(connections)

    def set_body(self, edge_id, from_junction, to_virtual_junction, lanes, f_speed, distance):
        self.edge_id = edge_id
        self.from_junction = from_junction
        self.to_virtual_junction = to_virtual_junction
        self.lanes = lanes
        self.f_speed = f_speed
        self.distance = distance

    def set_junction(self):
        if len(self.heads) == 0:
            self.to_junction = self.to_virtual_junction

    def print_edge(self):
        edge_string = '{"id": "%s", ' % self.edge_id + '"distance": %s, ' % self.distance + '"lanes": %s, ' % self.lanes + \
                      '"to_junction": "%s", ' % self.to_junction + '"from_junction": "%s", ' % self.from_junction + \
                      '"to": ['
        for other_edge in self.to:
            edge_string += '"%s", ' % other_edge
        cleaned_string = edge_string[:-2] if len(self.to) > 0 else edge_string
        edge_string = cleaned_string + '], "heads": ['
        for head in self.heads:
            edge_string += '"%s", ' % head
        cleaned_string = edge_string[:-2] if len(self.heads) > 0 else edge_string
        return cleaned_string + '], "f_speed": %s},' % self.f_speed


class Junction:
    def __init__(self, junction_id):
        self.tl = None
        self.phases = None
        self.junction_id = junction_id
        self.edges_from_me = []

    def add_tl_data(self, tl, phases):
        self.tl = tl
        self.phases = phases

    def add_edge(self, edge):
        self.edges_from_me.append(edge)

    def print_junction(self):
        junction_string = '"%s": {' % self.junction_id + '"tl": "%s",' % self.tl + '"phases": ['
        for phase in self.phases:
            junction_string += '{"duration": %s, ' % phase.duration + '"heads": ['
            for head in phase.heads:
                junction_string += '"%s", ' % head
            junction_string = junction_string[:-2] + ']},'
        return junction_string[:-1] + ']},'


class Phase:
    def __init__(self, duration, state):
        self.duration = duration
        self.heads = set()
        self.state = state

    def add_head(self, head):
        self.heads.add(head)


NetworkData('.../network.net.xml', '.../input_network_data.json')
