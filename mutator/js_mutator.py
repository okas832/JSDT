#python=3.7

import esprima
from esprima.scanner import RegExp
import json
import os
import re
import pexpect
import requests
import atexit
from random import randrange


esprima_obj=[esprima.nodes.TemplateElement.Value,RegExp]
esprima_ignore=[esprima.scanner.SourceLocation,esprima.scanner.Position]
def ast_to_json(ast):
    rtn=dict()
    for key,val in ast.items():
        if isinstance(val,esprima.nodes.Node) :
            rtn[key]=ast_to_json(val)
        elif type(val) in esprima_obj:
            rtn[key]=ast_to_json(val.__dict__)
        elif type(val) in esprima_ignore:
            continue
        elif isinstance(val,list):
            rtn[key]=list()
            for ele in val:
                rtn[key].append(ast_to_json(ele))
        elif type(val) in (int,str,bool) or (val is None): 
            if key=='isAsync':
                rtn["async"]=val
            else:
                rtn[key]=val
        elif isinstance(val,re.Pattern) and 'value'==key and 'regex' in ast.keys():
            rtn[key]=dict()
        else:
            print(ast)
            print(key)
            print(val)
            raise Exception

    if "type" in ast.keys() and ast.type=="ArrowFunctionExpression":
        rtn["id"]=None
    return rtn


class code_mutator():
    '''
    mutation unit
    class objects:
        - mutation_op_case: list of possible mutation. For each Experssions, there are many operations possible.
         mutation_op_case cluster each operation groups into smaller operation groups that are possible to commute without syntantic errors.
         For example, ("<<" , ">>" , ">>>") are possible to be mutated to each others, but they cannot mutate to "in" even though they are grouped by "Binary operation".
    '''
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
    class_cnt=0
    dirpath=os.path.dirname(os.path.abspath(__file__))
    js_server=pexpect.spawn(f"node {dirpath}/js_codegen/codegen_server.js",encoding='utf-8')
    atexit.register(js_server.close)
    js_server.expect("server is running...")
    js_server.expect("\n")
    port_num=int(js_server.before)
    
    
    def __init__(self,program,mut_mode="random"):
        '''
        program: strings of target program
        mut_mode: mutation mode. This will be applied when generate mutate(gen_mutant)

        instance objects:
            - node_history: list of (original_op,mutating_op,loc,node class).
              node class is used for rolling back. Do not directly extract information
        '''
        assert isinstance(program,str)
        self.code=program
        self.mut_cnt=0
        self.mut_mode=mut_mode
        self.recent_mut=None
        self.node_list=[]
        self.parsed=esprima.parseScript(program,delegate=self.mutant_cand_stack,loc=True)
        self.node_history=[]

    def mutant_cand_stack(self,node,metadata):
        '''
        stack nodes that are possible to mutate
        '''
        if node.type in code_mutator.mutation_op_case.keys():
            for exchangable_op in code_mutator.mutation_op_case[node.type]:
                if node.operator in exchangable_op and len(exchangable_op)>1:
                    self.node_list.append(node)
                    break
            else:
                print("operation in invalid node")
                raise Exception()
    
    def gen_code(self):
        res=requests.post(f'http://127.0.0.1:{code_mutator.port_num}/',data=json.dumps(ast_to_json(self.parsed)).replace("\\'","\'"))
        assert res.status_code==200
        return res.text

    def gen_mutant(self):
        '''
        generate mutant code (string) given condition 'mut_mode'
        '''
        # mutate AST
        if self.mut_mode=="random":
            target_node=self.node_list.pop(randrange(len(self.node_list))) # try catch for empty case(future)
            while (target_node.operator in (',','in','instanceof','typeof','void','delete')):
                target_node=self.node_list.pop(randrange(len(self.node_list)))
            # do specfic protocol for each expressions (future)

            if target_node.type in code_mutator.mutation_op_case.keys():
                for exchangable_op in code_mutator.mutation_op_case[target_node.type]:
                    if target_node.operator in exchangable_op:
                        i=exchangable_op.index(target_node.operator)
                        j=randrange(len(exchangable_op)-1)
                        target_node.operator=exchangable_op[j if i>j else j+1]
                        self.node_history.append((i,j if i>j else j+1,target_node.loc,target_node))
            else:
                # mutation is not available
                return None

        else:
            print("no possible mutation") ## raise exception (future)
            return None

        # make mutant code with AST
        return self.gen_code()
    
    def roll_back(self):
        '''
        roll back code from recent mutation
        '''
        i,j,_,node=self.node_history.pop()
        assert node.operator==j
        node.operator=i

        
        
        


if __name__ == "__main__":
    '''
    exmample code for 
    '''
    dirname=os.path.dirname(os.path.abspath(__file__))+'/examples'
    with open(f"{dirname}/test.js","r") as f:
        program=f.read()
    mut_manager=code_mutator(program)
    mut_program=mut_manager.gen_mutant()
    with open(f"{dirname}/test_mut.js","w") as g:
        g.write(mut_program)
    