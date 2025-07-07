import re

import js2py_

from .dom import MockDocument

FUNCTION_PATTERN = re.compile(r'function [a-zA-Z]+\(\) ({.+})')
EQUAL_PATTERN = re.compile(r'(![a-zA-Z]{5}\|\|[a-zA-Z]{5})==([a-zA-Z]{5})')


def solve_ui_metrics(ui_metrics: str) -> str:
    match = FUNCTION_PATTERN.search(ui_metrics)
    if not match:
        raise ValueError('No function pattern found in ui_metrics input')
    inner_function = match.group(1)
    # Replace '==' with '===' to ensure proper object comparison in js2py
    inner_function = EQUAL_PATTERN.sub(r'\1===\2', inner_function)
    context = js2py_.EvalJs()
    context.document = MockDocument()
    function = 'function main()' + inner_function
    context.eval(function)
    return str(context.main()).replace('\'', '"')
