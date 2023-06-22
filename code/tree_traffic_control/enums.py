
from enum import Enum


class CostType(Enum):
    TRUNK_CURRENT = 'current_trunk_cost'
    TREE_CURRENT = 'current_cost'
    TREE_CURRENT_DIVIDED = 'current_cost_divided'
    TREE_CUMULATIVE = 'cumulative_cost'
    TREE_CUMULATIVE_DIVIDED = 'cumulative_divided_cost'
    TREE_CUMULATIVE_DIVIDED_LTD = "tree_cumulative_divided_ltd"
    TREE_CUMULATIVE_LTD = "tree_cumulative_ltd"


class TreeTypes(Enum):
    SINGLE_FATHER = 'single_father'
    MULTI_FATHER = 'multi_father'


class AlgoType(Enum):
    NAIVE = 'naive'
    BABY_STEPS = 'baby_steps'
    PLANNED = 'planned'
    RANDOM = 'random'
    UNIFORM = 'uniform'
