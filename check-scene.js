const fs = require('fs');
const raw = fs.readFileSync('C:\\Users\\Administrator\\Downloads\\2026\\web-mobile\\assets\\main\\import\\01\\017ee6cad.b1a4a.json', 'utf8');
const data = JSON.parse(raw);

console.log('=== File Structure ===');
console.log('Type:', Array.isArray(data) ? 'Array' : typeof data);
console.log('Length/Keys:', Array.isArray(data) ? data.length : Object.keys(data));

// Check if it's the first element
const d = Array.isArray(data) ? data : data;

console.log('\n=== Elements ===');
for (let i = 0; i < Math.min(d.length || 0, 10); i++) {
    const elem = d[i];
    if (Array.isArray(elem)) {
        console.log(`d[${i}]: [Array, len=${elem.length}]`);
    } else if (typeof elem === 'object') {
        console.log(`d[${i}]: {Object}`);
    } else {
        console.log(`d[${i}]: ${typeof elem} = ${String(elem).substring(0, 50)}`);
    }
}

// Look for types
if (d[2] && Array.isArray(d[2])) {
    console.log('\n=== Looking in d[2] (names) ===');
    console.log('d[2]:', d[2].slice(0, 10));
}

if (d[3] && Array.isArray(d[3])) {
    console.log('\n=== d[3] content (first few) ===');
    for (let i = 0; i < Math.min(d[3].length, 5); i++) {
        const t = d[3][i];
        if (typeof t === 'string') {
            console.log(`d[3][${i}] (string): ${t.substring(0, 50)}`);
        } else if (Array.isArray(t)) {
            console.log(`d[3][${i}] (array): [${t.length}] ${String(t[0]).substring(0, 40)}`);
        }
    }
}
