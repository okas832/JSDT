from random import randrange
from .basic_node_mutator import basic_node_mutator

class node_mutator(basic_node_mutator):
    mutation_op_case={
    "UpdateExpression":(("++" , "--"),),
    "BinaryExpression":(("==" , "!=" , "===" , "!==") 
        , ("<" , "<=" , ">" , ">=")
        , ("<<" , ">>" , ">>>")
        , ("+" , "-" , "*" , "/" , "%")
        , (",") 
        , ("^" , "&") 
        , ("in")
        , ("instanceof")),
    "AssignmentExpression":(("=" , "+=" , "-=" , "*=" , "/=" , "%=")
        , ("<<=" , ">>=" , ">>>=")
        , ("|=" , "^=" , "&=")),
    "LogicalExpression":(("||" , "&&"),),
    "UnaryExpression":(("-" , "+" , "!" , "~" )
        , ("typeof") 
        , ("void") 
        , ("delete"))
    }

    def collect_mutable_node(self,node,metadata):
        '''
        stack nodes that are possible to mutate
        '''
        if node.type in node_mutator.mutation_op_case.keys():
            for exchangable_op in node_mutator.mutation_op_case[node.type]:
                if node.operator in exchangable_op and len(exchangable_op)>1 :
                    self.node_list.append(node)
                    break
            else:
                print("operation in invalid node")
                raise Exception()
    
    def random_mutate(self):
        target_node=self.node_list.pop(randrange(len(self.node_list))) # try catch for empty case(future)
        self.node_list_used.append(target_node)
        if (not self.node_list):
            self.node_list=self.node_list_used
            self.node_list_used=[]
            self.recycling+=1
        
        for exchangable_op in node_mutator.mutation_op_case[target_node.type]:
            if target_node.operator in exchangable_op:
                indexBefore=exchangable_op.index(target_node.operator)
                
                indexAfter=randrange(len(exchangable_op)-1)
                if indexAfter>indexBefore: indexAfter+=1
                
                target_node.operator=exchangable_op[indexAfter]
                self.history.append((exchangable_op[indexBefore],exchangable_op[indexAfter],target_node,self.op_name(__file__)))
                break