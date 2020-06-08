var fs = require('fs')
var util=require('util')
try {
    var escodegen = require('escodegen')
} catch (e){
    var exec=require('child_process').execSync
    exec (util.format("cd %s && npm install",__dirname))
    var escodegen = require('escodegen')
}
var parsed = JSON.parse(fs.readFileSync(util.format("%s/json_tmp",__dirname),"utf8"))
var file = fs.openSync(util.format("%s/testfile.js",__dirname),'w')

var newCode
parsed.body.forEach(element => {
    newCode = escodegen.generate(element)
    fs.writeSync(file,newCode)
    fs.writeSync(file,"\n")
    
})

fs.closeSync(file)