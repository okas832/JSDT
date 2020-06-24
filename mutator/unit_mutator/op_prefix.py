from random import randrange
from .basic_node_mutator import basic_node_mutator

class node_mutator(basic_node_mutator):
    

    mutation_op_case="UpdateExpression"

    def collect_mutable_node(self,node,metadata):
        '''
        stack nodes that are possible to mutate
        '''
        if node.type == node_mutator.mutation_op_case:
            self.node_list.append(node)
    
    def random_mutate(self):
        target_node=self.node_list.pop(randrange(len(self.node_list))) # try catch for empty case(future)
        self.node_list_used.append(target_node)
        if (not self.node_list):
            self.node_list=self.node_list_used
            self.node_list_used=[]
            self.recycling+=1

        target_node.prefix= False if target_node.prefix else True
        self.history.append((not target_node.prefix,target_node.prefix,target_node,self.op_name(__file__)))