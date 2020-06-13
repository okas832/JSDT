from py_mini_racer import py_mini_racer as pmr

# Supporting console functions in test codes
# need to override console functions, such as console.log, console.err, etc
# and when execution is complete, collect the results
def override_console(ctx):
  ovrr_file = open("v8/override_console.js", 'r')
  ctx.eval(ovrr_file.read())

def snapshot_console(ctx):
  console_stack = ctx.eval("log_stack")
  return console_stack

class V8bridge():
  # Setup a JS evaluation context
  def __init__(self):
    self.ctx = pmr.MiniRacer()
    override_console(self.ctx)
  
  # eval a source code string
  def eval_source(self, source):
    self.ctx.eval(source)

  # eval a js file
  def eval_file(self, filename):
    with open(filename, 'r') as js_file:
      self.ctx.eval(js_file.read())
  
  # console output of js program is now stored at context's "log_stack"
  def result_console(self):
    return snapshot_console(self.ctx)

def test_js_file(filename):
  pass

test_js_file("js_test.js")