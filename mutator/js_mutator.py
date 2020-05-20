#python=3.7

import esprima
from esprima.scanner import RegExp
import json
import os
import re
from random import randrange

esprima_obj=[esprima.nodes.TemplateElement.Value,RegExp ]
def ast_to_json(ast):
    rtn=dict()
    for key,val in ast.items():
        if isinstance(val,esprima.nodes.Node) :
            rtn[key]=ast_to_json(val)
        elif type(val) in esprima_obj:
            rtn[key]=ast_to_json(val.__dict__)
        elif isinstance(val,list):
            rtn[key]=list()
            for ele in val:
                rtn[key].append(ast_to_json(ele))
        elif type(val) in (int,str,bool) or (val is None): 
            rtn[key]=val
        elif isinstance(val,re.Pattern) and 'value'==key and 'regex' in ast.keys():
            rtn[key]=dict()
        else:
            print(ast)
            print(key)
            print(val)
            raise Exception
    return rtn


class code_mutator():

    UpdateOp=("++" , "--")
    BinaryOp=(("==" , "!=" , "===" , "!==") 
        , ("<" , "<=" , ">" , ">=")
        , ("<<" , ">>" , ">>>")
        , ("+" , "-" , "*" , "/" , "%")
        , (",") 
        , ("^" , "&") 
        , ("in")
        , ("instanceof"))
    AssignmentOp=(("=" , "+=" , "-=" , "*=" , "/=" , "%=")
        , ("<<=" , ">>=" , ">>>=")
        , ("|=" , "^=" , "&="))
    LogicalOp=("||" , "&&")
    UnaryOp=(("-" , "+" , "!" , "~" )
        , ("typeof") 
        , ("void") 
        , ("delete"))

    def __init__(self,program,mut_mode="random"):
        assert isinstance(program,str)
        self.code=program
        self.mut_cnt=0
        self.mut_mode=mut_mode
        self.recent_mut=None

        self.target_node_type=[
            'UpdateExpression',
            'BinaryExpression',
            'AssignmentExpression',
            'LogicalExpression',
            'UnaryExpression',
        ]
        self.node_list=[]
        self.parsed=esprima.parseScript(program,delegate=self.fragile_code_stack)
    
    def fragile_code_stack(self,node,metadata):
        if node.type in self.target_node_type:
            self.node_list.append(node)
    
    def gen_mutant(self):
        # mutate AST
        if self.mut_mode=="random":
            target_node=self.node_list.pop(randrange(len(self.node_list))) # try catch for empty case(future)
            while (target_node.operator in (',','in','instanceof','typeof','void','delete')):
                target_node=self.node_list.pop(randrange(len(self.node_list)))
            # do specfic protocol for each expressions (future)

            if target_node.type=='UpdateExpression':
                target_node.operator='--' if '++'==target_node.operator else '++'

            elif target_node.type=='BinaryExpression':
                for exchangable_op in code_mutator.BinaryOp:
                    if target_node.operator in exchangable_op:
                        i=exchangable_op.index(target_node.operator)
                        j=randrange(len(exchangable_op)-1)
                        target_node.operator=exchangable_op[j if i>j else j+1]

            elif target_node.type=='AssignmentExpression':
                for exchangable_op in code_mutator.AssignmentOp:
                    if target_node.operator in exchangable_op:
                        i=exchangable_op.index(target_node.operator)
                        j=randrange(len(exchangable_op)-1)
                        target_node.operator=exchangable_op[j if i>j else j+1]

            elif target_node.type=='LogicalExpression':
                for exchangable_op in code_mutator.LogicalOp:
                    if target_node.operator in exchangable_op:
                        i=exchangable_op.index(target_node.operator)
                        j=randrange(len(exchangable_op)-1)
                        target_node.operator=exchangable_op[j if i>j else j+1]

            elif target_node.type=='UnaryExpression':
                for exchangable_op in code_mutator.UnaryOp:
                    if target_node.operator in exchangable_op:
                        i=exchangable_op.index(target_node.operator)
                        j=randrange(len(exchangable_op)-1)
                        target_node.operator=exchangable_op[j if i>j else j+1]

        else:
            print("no possible mutation") ## raise exception (future)
            return None

        # make mutant code with AST
        with open("json_tmp","w") as f:
            json_val=json.dumps(ast_to_json(self.parsed))
            json.dump(json_val,f)
        os.system(f'node {os.path.dirname(os.path.abspath(__file__))}\js_codegen\codegen.js')
        
        with open("testfile.js","r") as g:
            rst=g.read()
        os.remove("json_tmp")
        os.remove("testfile.js")
        return rst
        
        
        




if __name__ == "__main__":
    '''
    exmample code for 
    '''
    with open("examples/test.js","r") as f:
        program=f.read()
    mut_manager=code_mutator(program)
    mut_program=mut_manager.gen_mutant()
    with open("examples/test_mut.js","w") as g:
        g.write(mut_program)
    