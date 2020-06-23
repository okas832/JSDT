from mutator.js_mutator import code_mutator
from spidermonkey import Spidermonkey
from v8.v8_bridge import V8bridge
from differ.diff import diff
import pathlib
import sys
import signal

if len(sys.argv) != 2:
    print(f"Usage : {sys.argv[0]} <seeds_dir>")
    print("seeds_dir : path that contain seed to mutate")
    exit(0)

def handler():
    raise Exception("Timeout")

def get_seed(d):
    for f in d.iterdir():
        if f.is_dir():
            yield from get_seed(f)
        else:
            if f.is_file() and f.suffix == ".js":
                yield f

save_dir = pathlib.Path("report/")
if not save_dir.exists():
    save_dir.mkdir(0o775)
elif not save_dir.is_dir() or any(True for _ in save_dir.iterdir()):
    print(f"Report directory \"{save_dir}\" is not an empty directory.")
    exit(-1)

target_dir = pathlib.Path(sys.argv[1])
if not target_dir.is_dir():
    print(f"Seed code directory \"{target_dir}\" does not exist or is not a directory.")
    exit(-1)

signal.signal(signal.SIGALRM, handler)

for target_program in get_seed(target_dir):
    with target_program.open('r') as f:
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
                log_file = save_dir / target_program.relative_to(target_dir)
                log_file = log_file.with_suffix('.js.log')
                log_file.parent.mkdir(0o775, True, True)
                with log_file.open("wb") as p:
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

