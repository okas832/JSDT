from mutator.js_mutator import code_mutator
from spidermonkey import Spidermonkey
from v8.v8_bridge import V8bridge
from differ.diff import diff
import os
import sys
import signal

if len(sys.argv) != 2:
    print("Usage : %s <seeds_dir>"%(sys.argv[0]))
    print("seeds_dir : path that contain seed to mutate")
    exit(0)

def handler():
    raise Exception("Timeout")

def get_seed(d):
    for f in os.listdir(d):
        if os.path.isdir(d + f):
            yield from get_seed(d + f + "/")
        else:
            if f.endswith(".js"):
                yield d + f

save_dir = "report/"

target_dir = sys.argv[1] + ("" if sys.argv[1][-1] == "/" else "/")

signal.signal(signal.SIGALRM, handler)

for target_program in get_seed(target_dir):
    with open(target_program, "r") as f:
        Mutator = code_mutator(f.read())
        for i in range(10):
            try:
                m_code = Mutator.gen_mutant()
            except:
                break
            sm = Spidermonkey(early_script_file='-', code=m_code)
            signal.alarm(2)
            try:
                sm_out, sm_err = sm.communicate()
            except Exception as x:
                sm_out = b""
                sm_err = b"Timeout"
            signal.alarm(0)

            signal.alarm(2)
            v8 = V8bridge()
            try:
                v8.eval_source(m_code)
            except Exception as x:
                v8_out = ""
                if x.args[0] == "bTimeout":
                    v8_err = b"Timeout"
                elif isinstance(x.args[0], bytes):
                    v8_err = x.args[0]
                else:
                    v8_err = x.args[0].encode()
            else:
                v8_out = v8.result_console()
                v8_out = ("\n".join(v8_out) + "\n").encode()
                v8_err = "".encode()
            signal.alarm(0)
            report = diff(sm_out, sm_err, v8_out, v8_err)

            if report is not None:
                with open(save_dir + target_program.split("/")[-1] + ".log", "wb") as p:
                    p.write(m_code.encode())
                    p.write(b"----------------------------\n")
                    p.write(report[0])
                    p.write(b"\n")
                    p.write(report[1])
                    p.write(b"\n")
                    p.write(report[2])
                    p.write(b"\n")
                    p.write(report[3])
                    p.write(b"\n")

