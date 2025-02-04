import re
import subprocess

FUNCTION_PATTERN = re.compile(r'function [a-zA-Z]+\(\) ({.+})')

node_script = '''
(function () {
    try {
        jsdom = require('jsdom');
    } catch (error) {
        process.stdout.write(error.code);
        throw error;
    }
    const jsCode = process.argv.at(-1);
    const dom = new jsdom.JSDOM(`<!DOCTYPE html><html><body></body></html>`, {
        runScripts: 'dangerously'
    });
    dom.window.eval(jsCode);
    const result = dom.window.main();
    process.stdout.write(JSON.stringify(result));
})()
'''


def run_js_metrics(ui_metrics):
    match = FUNCTION_PATTERN.search(ui_metrics)
    if not match:
        raise ValueError('No matching function found in js.')
    inner_function = match.group(1)
    code = f'function main() {inner_function}'

    try:
        result = subprocess.check_output(['node', '-e', node_script, code], text=True)
    except FileNotFoundError:
        raise RuntimeError('Node.js is not installed.')
    except subprocess.CalledProcessError as e:
        if e.output == 'MODULE_NOT_FOUND':
            raise RuntimeError('jsdom module not found. Run "npm install jsdom" to install the module.')
        raise RuntimeError('ui_metrics execution failed.')

    return result
