# -*- coding: utf-8 -*-
u"""

.. moduleauthor:: Mark Hall <mark.hall@mail.room3b.eu>
"""

import math
import random
import re

dice_regexp = re.compile(r'([0-9]*)[Dd]([0-9]+)')
calculation_regexp = re.compile(r'((?:(?:\(?[0-9]*[dD][0-9]+)|(?:\(?[0-9]+))(?:(?:[0-9]*[dD][0-9]+)|(?:[0-9]+)|(?:[+\-*/()])|\s+)*)')
variable_regexp = re.compile(r'\{([a-zA-Z0-9_\-.]+)\}')
bool_if_regexp = re.compile(r'\{([0-9a-zA-Z_\-.]+)\s*\?\s*([0-9a-zA-Z_\-.]+)\s*:\s*([0-9a-zA-Z_\-.]+)\}')
cmp_if_regexp = re.compile(r'\{([0-9a-zA-Z_\-.]+)\s*\?\s*([0-9a-zA-Z_\-.]+)\s*==\s*(\'?[0-9a-zA-Z _\-.]+\'?)\s*:\s*([0-9a-zA-Z_\-.]+)\}')

OPERATORS = {'(': {'precedence': 0},
             '*': {'precedence': 2,
                   'params': 2,
                   'func': lambda a, b: a * b},
             '/': {'precedence': 2,
                   'params': 2,
                   'func': lambda a, b: a / b},
             '+': {'precedence': 1,
                   'params': 2,
                   'func': lambda a, b: a + b},
             '-': {'precedence': 1,
                   'params': 2,
                   'func': lambda a, b: a - b},
             'floor': {'precedence': 4,
                       'params': 1,
                       'func': math.floor},
             'max': {'precedence': 3,
                     'params': 2,
                     'func': max},
             'min': {'precedence': 3,
                     'params': 2,
                     'func': min}}

def token_type(string):
    if string in OPERATORS.keys():
        return ('op', string)
    else:
        return ('val', string)


def tokenise(string):
    tokens = []
    tmp = []
    mode = 0
    for c in string:
        if c in ['+', '-', '*', '/']:
            if tmp:
                tokens.append(token_type(''.join(tmp).strip()))
                tmp = []
            tokens.append(('op', c))
        elif c in ['(', ')']:
            if tmp:
                tokens.append(token_type(''.join(tmp).strip()))
                tmp = []
            tokens.append(('bra', c))
        elif c in ['{', '}']:
            if c == '{':
                if tmp:
                    tokens.append(token_type(''.join(tmp).strip()))
                    tmp = []
                mode = 1
            elif c == '}':
                mode = 0
            tmp.append(c)
        elif c == ' ':
            if mode == 0:
                if tmp: 
                    tokens.append(token_type(''.join(tmp).strip()))
                    tmp = []
            elif mode == 1:
                tmp.append(c)
        else:
            tmp.append(c)
    if tmp:
        tokens.append(token_type(''.join(tmp).strip()))
    return tokens


def add_dice(tokens):
    new_tokens = []
    for token in tokens:
        if token[0] == 'val':
            match = re.match(dice_regexp, token[1])
            if match:
                if match.group(1):
                    new_tokens.append(('bra', '('))
                    count = int(match.group(1))
                    for i in range(0, count):
                        new_tokens.append(('val', str(random.randint(1, int(match.group(2))))))
                        if i < count - 1:
                            new_tokens.append(('op', '+'))
                    new_tokens.append(('bra', ')'))
                else:
                    new_tokens.append(('val', str(random.randint(1, int(match.group(2))))))
            else:
                new_tokens.append(token)
        else:
            new_tokens.append(token)
    return new_tokens


def add_variables(tokens, values):
    new_tokens = []
    for token in tokens:
        if token[0] == 'val':
            if token[1].startswith('{') and token[1].endswith('}'):
                match = re.match(variable_regexp, token[1])
                if match:
                    if match.group(1):
                        if match.group(1) in values:
                            try:
                                if values[match.group(1)] is None:
                                    new_tokens.append(('val', '0'))
                                else:
                                    new_tokens.append(('val', str(values[match.group(1)])))
                            except:
                                new_tokens.append(('val', '0'))
                        else:
                            new_tokens.append(('val', '0'))
                    else:
                        try:
                            new_tokens.append(('val', str(random.randint(1, match.group(2)))))
                        except:
                            new_tokens.append(('val', '0'))
                else:
                    match = re.match(bool_if_regexp, token[1])
                    if match:
                        if match.group(2) in values:
                            if values[match.group(2)] and match.group(1) in values:
                                if values[match.group(1)] is None:
                                    new_tokens.append(('val', '0'))
                                else:
                                    new_tokens.append(('val', str(values[match.group(1)])))
                            elif not values[match.group(2)] and match.group(3) in values:
                                if values[match.group(3)] is None:
                                    new_tokens.append(('val', '0'))
                                else:
                                    new_tokens.append(('val', str(values[match.group(3)])))
                            else:
                                new_tokens.append(('val', '0'))
                        else:
                            new_tokens.append(('val', '0'))
                    else:
                        match = re.match(cmp_if_regexp, token[1])
                        if match:
                            if match.group(2) and match.group(2) in values and match.group(1) in values:
                                cmp_value = match.group(3)
                                if cmp_value.startswith("'") and cmp_value.endswith("'"):
                                    cmp_value = cmp_value[1:-1]
                                if values[match.group(2)] == cmp_value:
                                    if values[match.group(1)] is None:
                                        new_tokens.append(('val', '0'))
                                    else:
                                        new_tokens.append(('val', str(values[match.group(1)])))
                                elif match.group(4) in values:
                                    if values[match.group(4)] is None:
                                        new_tokens.append(('val', '0'))
                                    else:
                                        new_tokens.append(('val', str(values[match.group(4)])))
                                else:
                                    new_tokens.append(('val', '0'))
                            elif match.group(4) in values:
                                new_tokens.append(('val', str(values[match.group(4)])))
                            else:
                                new_tokens.append(('val', '0'))
                        else:
                            new_tokens.append(('val', '0'))
            else:
                new_tokens.append(token)
        else:
            new_tokens.append(token)
    return new_tokens


def op_precedence(op):
    return OPERATORS[op]['precedence']


def process_unary(tokens):
    output = []
    modifier = None
    for idx in range(0, len(tokens)):
        if (idx == 0 or tokens[idx - 1][0] == 'op') and idx < len(tokens) - 1 and tokens[idx][0] == 'op' and tokens[idx][1] == '-' and tokens[idx + 1][0] == 'val':
            modifier = '-'
        elif modifier:
            if tokens[idx][0] == 'val':
                if modifier == '-':
                    output.append(('val', str(int(tokens[idx][1]) * -1)))
            modifier = None
        else:
            output.append(tokens[idx])
    return output


def infix_to_postfix(tokens):
    stack = []
    output = []
    for token in tokens:
        if token[0] == 'val':
            output.append(token)
        elif token[0] == 'op':
            if not stack:
                stack.append(token[1])
            else:
                if op_precedence(stack[-1]) < op_precedence(token[1]):
                    stack.append(token[1])
                else:
                    while stack and op_precedence(stack[-1]) >= op_precedence(token[1]):
                        output.append(('op', stack.pop()))
                    stack.append(token[1])
        elif token[0] == 'bra':
            if token[1] == '(':
                stack.append('(')
            elif token[1] == ')':
                token = stack.pop()
                while stack and token != '(':
                    output.append(('op', token))
                    token = stack.pop()
    while stack:
        output.append(('op', stack.pop()))
    return output


def calculate(tokens):
    try:
        stack = []
        for token in tokens:
            if token[0] == 'val':
                value = float(token[1])
                if value.is_integer():
                    stack.append(int(value))
                else:
                    stack.append(value)
            elif token[0] == 'op':
                params = []
                for _ in range(0, OPERATORS[token[1]]['params']):
                    params.append(stack.pop())
                params.reverse()
                stack.append(OPERATORS[token[1]]['func'](*params))
        return stack.pop()
    except:
        return None
