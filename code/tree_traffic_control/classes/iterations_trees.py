from classes.current_load_tree import CurrentLoadTree
from enums import CostType


class IterationTrees:
    def __init__(self, iteration, links, cost_type: CostType):
        self.iteration = iteration
        self.alreadyInUsePerIteration = []
        self.current_links_in_load_tree = {}
        self.all_trees_per_iteration = {}
        self.all_trees_costs = []
        self.calc_spatial_load_trees(links, iteration, cost_type)

    def calc_spatial_load_trees(self, links, iteration, cost_type: CostType):
        """
        create tree by starting from branches that don't lead to a loaded segment.
        write on each branch the number of trees it is on.
        keep a tree even if it is a subtree, as long as its trunk is leading to a traffic-light
        """
        load_spatial_order = []
        for link in links:
            if link.is_loaded:
                if link.is_lead_to_tl:
                    load_spatial_order.append(link.link_id)
                    continue
                is_trunk = True
                for link_from_me in link.links_from_me:
                    if links[link_from_me].is_loaded:
                        is_trunk = False
                        break
                if is_trunk:
                    load_spatial_order.append(link.link_id)
        while len(load_spatial_order) > 0:
            working_on_link_id = load_spatial_order.pop(0)
            self.calc_one_spatial_load_tree(links, working_on_link_id)
        for tree in self.all_trees_per_iteration.values():
            tree.mark_link_fathers(links, iteration)
        for link in links:
            link.fill_my_cost_and_weight(iteration, cost_type)
        for tree in self.all_trees_per_iteration.values():
            tree.save_cost_on_branch(links, iteration)
        for tree in self.all_trees_per_iteration.values():
            tree.calc_spatial_cost(links, iteration)
            self.all_trees_costs.append(TreeCost(iteration, tree.current_cost))

    def calc_one_spatial_load_tree(self, links, trunk_id):
        this_tree = CurrentLoadTree(trunk_id)
        this_tree.add_link_to_spatial_tree(trunk_id, links, -1)
        self.all_trees_per_iteration[this_tree.trunk_link_id] = this_tree


class TreeCost:
    def __init__(self, iteration, cost):
        self.iteration = iteration
        self.cost = cost

