const http=require('http')
var util=require('util')

try {
    var escodegen = require('escodegen')
} catch (e){
    var exec=require('child_process').execSync
    exec (util.format("cd %s && npm install",__dirname))
    var escodegen = require('escodegen')
}

server=http.createServer((req,res)=>{

    var postdata='';
    
    req
    .on('error',(err)=>{
        console.error(err)
    })
    .on('data',(data)=>{
        postdata=postdata+data
    })
    .on('end',()=>{
        res.on('error',(err)=>{
            console.error(err)
        })
        var parsed=JSON.parse(postdata)
        var newCode=''
        parsed.body.forEach(element => {
            newCode = newCode+escodegen.generate(element)+"\n"
        })
        res.writeHead(200,{'Content-Type':'text/plain'})
        res.write(newCode)
        res.end()
    })
}).listen(()=>{
    console.log(util.format("server is running...%d\n",server.address().port))
})