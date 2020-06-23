#python=3.7

import esprima
from esprima.scanner import RegExp
import json
import os
import re
import pexpect
import requests
import atexit
from random import randrange, choice, seed


esprima_expr = [
    esprima.Syntax.ThisExpression,
    esprima.Syntax.Identifier,
    esprima.Syntax.Literal,
    esprima.Syntax.ArrayExpression,
    esprima.Syntax.ObjectExpression,
    esprima.Syntax.FunctionExpression,
    esprima.Syntax.ArrowFunctionExpression,
    esprima.Syntax.ClassExpression,
    esprima.Syntax.TaggedTemplateExpression,
    esprima.Syntax.MemberExpression,
    esprima.Syntax.Super,
    esprima.Syntax.MetaProperty,
    esprima.Syntax.NewExpression,
    esprima.Syntax.CallExpression,
    esprima.Syntax.UpdateExpression,
    esprima.Syntax.AwaitExpression,
    esprima.Syntax.UnaryExpression,
    esprima.Syntax.BinaryExpression,
    esprima.Syntax.LogicalExpression,
    esprima.Syntax.ConditionalExpression,
    esprima.Syntax.YieldExpression,
    esprima.Syntax.AssignmentExpression,
    esprima.Syntax.SequenceExpression
]
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
        elif type(val) in (int,float,str,bool) or (val is None):
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
        - mutation_consts: list of literals/objects to use as constant replacement. All esprima_expr (Expression) are subject to replacement.
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
    mutation_consts = tuple(  # TODO: generate constants more randomly for strings and objects ([], {})
        tuple(esprima.parseScript(const).body[0].expression for const in const_set) for const_set in [
            ['0', '-0', 'Infinity', '-Infinity', '1', '-1', '1.1', 'NaN'],
            ['true', 'false'],
            ['[]', '[0]', '[0, ({}), []]'],
            ['({})', '({aaa: "bbb"})'],
            ['""', '"a0b1c2"', '"\\x00"', '"\\u1234\\uabcd\\uffff"'],
            ['null', 'undefined']
        ]
    )
    class_cnt=0
    dirpath=os.path.dirname(os.path.abspath(__file__))
    js_server=pexpect.spawn(f"node {dirpath}/js_codegen/codegen_server.js",encoding='utf-8')
    atexit.register(js_server.close)
    js_server.expect("server is running...")
    js_server.expect("\n")
    port_num=int(js_server.before)
    
    
    def __init__(self,program,mut_mode="random",seg_loc_change=True):
        '''
        program: strings of target program
        mut_mode: mutation mode. This will be applied when generate mutate(gen_mutant)
        seg_loc_change: If it's true, code string will be replaced to code generated by AST of original code.
        While mutating code, mutated code does not preserve blank line and comments. This cause inconsistency of line number number between original code and mutated code.
        seg_loc_change is to compensate the abnormality
        instance objects:
            - node_history: list of (mutation type, loc, node class, *rollback_info).
              node class is used for rolling back. Do not directly extract information
        '''
        assert isinstance(program,str)
        self.code=program
        self.mut_cnt=0
        self.mut_mode=mut_mode
        self.recent_mut=None
        self.node_list=[]
        self.node_list_used=[]
        self.recycling=0 # number of recyling of node
        
        if seg_loc_change:
            self.parsed=esprima.parseScript(program)
            self.parsed=esprima.parseScript(self.gen_code(),delegate=self.mutant_cand_stack,loc=True)
        else:
            self.parsed=esprima.parseScript(program,delegate=self.mutant_cand_stack,loc=True)
        self.node_history=[]

    def mutant_cand_stack(self,node,metadata):
        '''
        stack nodes that are possible to mutate
        '''
        if node.type in code_mutator.mutation_op_case.keys():
            for exchangable_op in code_mutator.mutation_op_case[node.type]:
                if node.operator in exchangable_op and len(exchangable_op)>1 :
                    self.node_list.append(node)
                    break
            else:
                print("operation in invalid node")
                raise Exception()
        elif node.type in esprima_expr:  # constant replacement, precedence less than op mutation
            self.node_list.append(node)
    
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
            if (not self.node_list):  # rollback each time we've depleted node_list
                while self.node_history:
                    self.roll_back()
                self.node_list=self.node_list_used
                self.node_list_used=[]
                self.recycling+=1
            target_node=self.node_list.pop(randrange(len(self.node_list))) # try catch for empty case(future)
            self.node_list_used.append(target_node)

            # do specfic protocol for each expressions (future)

            if target_node.type in code_mutator.mutation_op_case.keys():
                for exchangable_op in code_mutator.mutation_op_case[target_node.type]:
                    if target_node.operator in exchangable_op:
                        i = exchangable_op.index(target_node.operator)
                        j = randrange(len(exchangable_op) - 1)
                        if i <= j:
                            j += 1
                        target_node.operator = exchangable_op[j]
                        self.node_history.append((0, target_node.loc, target_node, exchangable_op[i], exchangable_op[j]))
            elif target_node.type in esprima_expr:
                const_set = choice(code_mutator.mutation_consts)
                replace_expr = choice(const_set)
                prev_expr = esprima.nodes.Node()
                code_mutator.replace_items(prev_expr, target_node)     # backup
                code_mutator.replace_items(target_node, replace_expr)  # in-place replace
                self.node_history.append((1, prev_expr.loc, target_node, prev_expr))
            else:
                # mutation is not available
                return None

        else:
            print("no possible mutation option") 
            return None

        # make mutant code with AST
        return self.gen_code()
    
    def roll_back(self):
        '''
        roll back code from recent mutation
        '''
        mutation_type, _, target_node, *rbinfo = self.node_history.pop()
        if mutation_type == 0:
            assert target_node.operator == rbinfo[1]
            target_node.operator = rbinfo[0]
        elif mutation_type == 1:
            code_mutator.replace_items(target_node, rbinfo[0])
        else:
            print("Invalid mutation type at rollback")
            raise Exception()

    def replace_items(dst, src):
        dst_items, src_items, src_keys = dst.items(), src.items(), src.keys()
        for k, v in src_items:
            dst.__setattr__(k, v)
        for k, v in dst_items:
            if k not in src_keys:
                dst.__setattr__(k, None)
        
        


if __name__ == "__main__":
    '''
    exmample code for 
    '''
    #seed(0xdeadbeef)  ### seeding for reproducible debugging
    dirname=os.path.dirname(os.path.abspath(__file__))+'/examples'
    with open(f"{dirname}/test.js","r") as f:
        program=f.read()
    mut_manager=code_mutator(program)
    ori_program=mut_manager.gen_code()

    for _ in range(100):
        mut_program=mut_manager.gen_mutant()
        print(f"mutation occurs at line {mut_manager.node_history[-1][1].start.line}")
    with open(f"{dirname}/test_origin.js","w") as g:
        g.write(ori_program)

    with open(f"{dirname}/test_mut.js","w") as g:
        g.write(mut_program)
    
    
