var fs = require('fs')
var escodegen = require('escodegen')
var parsed = JSON.parse(JSON.parse(fs.readFileSync('json_tmp',"utf8")))
var file = fs.openSync('testfile.js','w')

var newCode
parsed.body.forEach(element => {
    newCode = escodegen.generate(element)
    fs.writeSync(file,newCode)
    fs.writeSync(file,"\n")
    
})

fs.closeSync(file)