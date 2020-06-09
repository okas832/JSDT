// burrowed idea from
// https://stackoverflow.com/questions/7042611/override-console-log-for-production
var console = {};

log_stack = new Array(0),
err_stack = new Array(0),

console.log = function(text) {
  log_stack.push(text);
}

console.err = function(text) {
  err_stack.push(text);
}