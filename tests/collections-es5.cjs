/* The bundled Acorn accepts block declarations in ES5: reject them explicitly. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const acorn=require(process.argv[2]||'C:/tizen-studio/tools/jsa/jalangi/node_modules/acorn/acorn.js');
function check(source){const ast=acorn.parse(source,{ecmaVersion:5,locations:true});function walk(node,parent,grandparent){if(!node||typeof node!=='object')return;if(node.type==='FunctionDeclaration'&&parent&&parent.type==='BlockStatement')assert.ok(grandparent&&/Function/.test(grandparent.type),'Nonportable ES5 function declaration inside a statement block at line '+node.loc.start.line);for(const key in node){if(key==='loc')continue;const v=node[key];if(Array.isArray(v))v.forEach(x=>walk(x,node,parent));else if(v&&typeof v==='object')walk(v,node,parent);}}walk(ast);}
assert.throws(()=>check("'use strict';if(true){function unsupported(){}}"),/Nonportable/);
for(const name of ['collections.js','player.js','browse-prefs.js','floating-player.js'])check(fs.readFileSync(path.join(__dirname,'../public/tv',name),'utf8'));
console.log('PASS: ES5 syntax plus explicit rejection of statement-block function declarations; independent MAG exit shell parsed separately.');
