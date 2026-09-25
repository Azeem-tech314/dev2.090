// Extract PLACES array from raw v2 snippet and emit data/indies.json
const fs = require('fs');
const raw = fs.readFileSync('tools/indies_raw.js', 'utf8');
// Wrap and eval
const wrapped = 'var out = ' + raw.replace(/^\s*var\s+PLACES\s*=/, '') + '; return out;';
const PLACES = new Function(wrapped)();
console.log('Extracted', PLACES.length, 'indie spots');
fs.mkdirSync('data/compact', {recursive:true});
fs.writeFileSync('data/compact/indies.json', JSON.stringify(PLACES));
console.log('Wrote data/compact/indies.json', (fs.statSync('data/compact/indies.json').size/1024).toFixed(1)+' KB');
