
class LoadTreeBranch:
    def __init__(self, link_id, father_id):
        self.link_id = link_id
        self.father_id = father_id
        self.link_ids_to_be_added = []
        self.current_cost = 0
        self.current_cost_for_tree = 0

    def map_potential_spatial_sons(self, links, tree_leafs_list):  # adding a link (LoadTreeBranch) to a tree
        found_a_son = False
        for potential_son_link_id in links[self.link_id].links_to_me:  # check its sons
            potential_son_link = links[potential_son_link_id]
            if potential_son_link.is_loaded:
                self.link_ids_to_be_added.append(potential_son_link.link_id)
                found_a_son = True  # found a son which is a branch
        if not found_a_son:  # if it has no sons, it can be added as a leaf
            tree_leafs_list.append(self.link_id)

    def set_current_cost(self, current_cost_for_tree, current_cost):
        self.current_cost_for_tree = current_cost_for_tree
        self.current_cost = current_cost
