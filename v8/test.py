from py_mini_racer import py_mini_racer as pmr

def eval_js(jsexpr):
  ctx = pmr.MiniRacer()
  return ctx.eval(jsexpr)

def eval_from_file(filename):
  jsfile = open(filename, 'r')
  ctx = pmr.MiniRacer()
  return ctx.eval(jsfile.read())

def main():
  # expr01 = 'var f1 = () => "hello, v8!"; f1()'
  # print(eval_js(expr01))
  print(eval_from_file("./input/sample01.js"))

main()