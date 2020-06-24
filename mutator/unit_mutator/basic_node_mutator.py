import os

class basic_node_mutator():
    
    def __init__(self,code_mutator_history):
        self.history=code_mutator_history

        self.node_list=[]
        self.node_list_used=[]
        self.recycling=0 # number of recycling of node
    
    def collect_mutable_node(self,node,metadata):
        pass

    def random_mutate(self):
        pass

    def op_name(self,file_name):
        return os.path.split(file_name)[-1][:-3]