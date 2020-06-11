from py_mini_racer import py_mini_racer as pmr

def get_js_context():
  return pmr.MiniRacer()

# Supporting console functions in test codes
# need to override console functions, such as console.log, console.err, etc
# and when execution is complete, collect the results
def override_console(ctx):
  ovrr_file = open("override_console.js", 'r')
  ctx.eval(ovrr_file.read())

def collect_console(ctx):
  pass

def test_js_file(filename):
  # first make js context for testing
  ctx = get_js_context()
  override_console(ctx)
  # open target js code, and eval it in context
  js_file = open(filename, 'r')
  ctx.eval(js_file.read())
  # finally print the resulting context's result
  console_result = ctx.eval("log_stack")
  print(console_result)

test_js_file("js_test.js")