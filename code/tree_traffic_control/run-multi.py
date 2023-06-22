from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
from pathlib import Path

import runner

sys.path.append(os.path.join('d:', os.sep, 'Program Files (x86)', 'Eclipse', 'Sumo', 'tools'))
# sys.path.append(os.path.join('c:', os.sep, 'whatever', 'path', 'to', 'sumo', 'tools'))

from sumolib import checkBinary  # noqa
import traci  # noqa
from enums import CostType, AlgoType

_nogui = True

from classes.run_config import RunConfig

# config:
input_network_file = '../input_network_data.json'


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


def print_results(results_data):
    for measure in ['ended_vehicles_count', 'started_vehicles_count', 'time per v']:
        print_one_file(results_data, measure)


def print_one_file(results_data, measure):
    file_name = common_path + '/res_' + measure + '.txt'
    source_file = open(file_name, 'w')
    header = ''
    for experiment_name in results_data[0].keys():
        header += "," + experiment_name
    print(header, file=source_file)
    for inx, iteration_data in enumerate(results_data):
        line = str(inx)
        for experiment_name in results_data[0].keys():
            line += "," + str(results_data[inx][experiment_name][measure])
        print(line, file=source_file)


def print_config_data(config_run, path):
    source_file = open(path + '/configurations.txt', 'w')
    for this_config_data in config_run:
        print(this_config_data, file=source_file)


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    options.nogui = _nogui
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    common_path = '.../ExperimentFolder'
    paths = [# '1',
             '5'
        # , '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'
             # '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40'
        #'41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60'
         #'61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80'
        #'81', '82', '83', '84', '85'
    ]
    configurations = [
        RunConfig(False, 'CurrentTreeDvd', CostType.TREE_CURRENT_DIVIDED, AlgoType.BABY_STEPS),
        RunConfig(True, 'SUMOActuated', CostType.TREE_CURRENT_DIVIDED, AlgoType.BABY_STEPS),
        # RunConfig(False, 'Random', CostType.TREE_CURRENT_DIVIDED, AlgoType.RANDOM),
        # RunConfig(False, 'Uniform', CostType.TREE_CURRENT_DIVIDED, AlgoType.UNIFORM),
    ]
    results = []
    for iteration, exp_path in enumerate(paths):
        results.append({})
        config_data = []
        for conf in configurations:
            method_dir = common_path + '/' + exp_path + '/' + conf.name
            Path(method_dir).mkdir(parents=True, exist_ok=True)
            res = runner.run(sumoBinary, common_path + '/' + exp_path, method_dir, input_network_file, conf)
            results[iteration][conf.name] = res
            config_data.append(conf.print_me_to_string())
        print_config_data(config_data, common_path + '/' + exp_path)
    print_results(results)
