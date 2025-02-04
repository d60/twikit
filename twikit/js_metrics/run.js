import { JSDOM } from 'jsdom';


const jsCode = process.argv.at(-1)
const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`, {
    runScripts: 'dangerously'
});

dom.window.eval(jsCode);

const result = dom.window.main();
console.log(JSON.stringify(result));
