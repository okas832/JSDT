from mutator.js_mutator import code_mutator
from spidermonkey import Spidermonkey
from v8.v8_bridge import V8bridge
from differ.diff import diff

if __name__ == "__main__":
    target_program = "./input/sample01.js"
    with open(target_program, "r") as f:
        Mutator = code_mutator(f.read()+"\nf();\n")
        code = Mutator.gen_code()
        m_code = Mutator.gen_mutant()

        sm = Spidermonkey(early_script_file='-', code=m_code)
        sm_out, sm_err = sm.communicate()

        v8 = V8bridge()
        try:
            v8.eval_source(m_code)
        except Exception as x:
            v8_out = ""
            v8_err = x.args[0].encode()
        else:
            v8_out = v8.result_console()
            v8_out = ("\n".join(v8_out) + "\n").encode()
            v8_err = "".encode()

        report = diff(sm_out, sm_err, v8_out, v8_err)
        if report is not None:
            print(report)
