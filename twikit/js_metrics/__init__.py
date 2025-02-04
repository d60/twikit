import re
import subprocess

FUNCTION_PATTERN = re.compile(r'function [a-zA-Z]+\(\) ({.+})')


def run_js_metrics(js):
    match = FUNCTION_PATTERN.search(js)
    if not match:
        raise ValueError('No matching function found in js.')
    inner_function = match.group(1)
    code = f'function main() {inner_function}'
    try:
        result = subprocess.check_output(['node', 'run.js', code])
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'ui_metrics execution failed.') from e
    return result.decode()
