from classes.load_tree_branch import LoadTreeBranch
from enums import CostType


class CurrentLoadTree:
    def __init__(self, trunk_link_id):
        self.trunk_link_id = trunk_link_id
        self.all_my_branches = {}  # key: link_id, value: LoadTreeBranch
        self.all_my_leafs = []
        self.uniqueKey = str(trunk_link_id)
        self.current_cost = 0
        self.current_trunk_cost = 0

    def add_link_to_spatial_tree(self, branch_to_be_added, links, my_father):
        link_id = branch_to_be_added
        this_branch = LoadTreeBranch(link_id, my_father)
        self.all_my_branches[link_id] = this_branch
        this_branch.map_potential_spatial_sons(links, self.all_my_leafs)

        while len(this_branch.link_ids_to_be_added) > 0:
            next_branch_to_be_added = this_branch.link_ids_to_be_added[0]
            this_branch.link_ids_to_be_added.pop(0)
            if next_branch_to_be_added not in self.all_my_branches:
                self.add_link_to_spatial_tree(next_branch_to_be_added, links, link_id)

    def get_cost_by_type(self, cost_type):
        if cost_type == CostType.TREE_CURRENT_DIVIDED.name:
            return self.current_cost
        return 0

    def mark_link_fathers(self, links, iteration):
        for b in list(self.all_my_branches.values()):
            if iteration not in links[b.link_id].in_tree_fathers:
                links[b.link_id].in_tree_fathers[iteration] = []
            links[b.link_id].in_tree_fathers[iteration].append(b.father_id)

    def calc_spatial_cost(self, links, iteration):
        self.current_trunk_cost = links[self.trunk_link_id].iteration_data[iteration].current_cost_minutes
        for link_id in list(self.all_my_branches.keys()):
            self.current_cost += links[link_id].cost_data_per_iter[iteration].current_cost_for_tree

    def save_cost_on_branch(self, links, iteration):
        for link_id in list(self.all_my_branches.keys()):
            self.all_my_branches[link_id].set_current_cost(links[link_id].cost_data_per_iter[iteration].current_cost_for_tree,
                                                           links[link_id].cost_data_per_iter[iteration].current_cost)



