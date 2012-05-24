#!/usr/bin/env python

# Copyright (C) 2012, Valentin Lorentz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Converts an assembly file into a load file."""

from __future__ import print_function

__all__ = ['Assembler', 'ParseError']

import re
import core

class SYNTAX:
    addressing = '#$*@{}<>'
    _label_list = '\s*(?P<labels>([A-Z_][0-9A-Z_]+(:|\s)\s*)+)'
    label_list = re.compile(_label_list)
    line = re.compile(('%s?'
                       '\s*(?P<opcode>[A-Z]{3})'
                       '(.(?P<modifier>[A-Z]{1,2}))?'
                       '(\s+(?P<A>[%s]?[^ \t\n\r\f\v,]+)(\s*,\s*(?P<B>[%s]?\S+))?)?'
                       '\s*(;.*)?'
                      ) % (_label_list, addressing, addressing)
                     )
    comment_line = re.compile('^\s*(;.*)?$')

    opcodes = ('DAT MOV ADD SUB MUL DIV MOD JMP JMZ JMN DJN SPL CMP SEQ SNE '
            'SLT LDP STP NOP ORG EQU END').split()
    modifiers = 'A B AB BA F I X'.split()

class ParseError(Exception):
    pass


class Assembler(object):
    def __init__(self, properties):
        if not isinstance(properties, core.MarsProperties):
            raise ValueError('`properties` must be an instance of '
                    'core.MarsProperties, not %r' % properties)
        self._properties = properties

    def assemble(self, assembly, raw=False):
        if not isinstance(assembly, str):
            raise ValueError('The assembly code must be a string, not %r' %
                    assembly)

        def evaluate_operand(operand):
            if operand is None or operand == '':
                return None
            addresser = operand[0] if operand[0] in SYNTAX.addressing else ''
            operand = operand[len(addresser):]
            for x in operand:
                if x not in ('abcdefghijklmnopqrstuvwxyz'
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/%'):
                    raise ParseError('On line %i: `%s` is not a valid '%(j,x)+
                            'character')
            context = self._properties.as_dict
            context.update(constants)
            context.update(dict([(x,y-i) for x,y in labels.items()]))
            context.update(variables)
            return addresser + str(eval(operand, context))


        origin = 0
        labels = {}
        constants = {}
        variables = {}
        load_queue = []
        i = 0 # Line in the load file
        old_label = None
        for (j, line) in enumerate(assembly.split('\n')):
            label = None
            if SYNTAX.comment_line.match(line):
                continue
            tokens = [x for x in line.split(' ') if x != '']
            if tokens[0].split('.')[0] not in SYNTAX.opcodes:
                label = tokens.pop(0)
                if label.endswith(':'):
                    label = label[0:-1]
            else:
                label = None
            if tokens == []:
                raise ParseError('On line %i: `%s` is not a valid opcode.' %
                        (j, label))
            splitted = tokens.pop(0).upper().split('.')
            if splitted[0] not in SYNTAX.opcodes:
                raise ParseError('On line %i: `%s` is not a valid opcode.' %
                        (j, splitted[0]))
            if len(splitted) > 2:
                raise ParseError('On line %i: `%s` ' % (j, tokens[0]) +
                        'is not a valid opcode.modifier syntax.')
            opcode = splitted[0]
            if len(splitted) == 2:
                if splitted[1] not in SYNTAX.modifiers:
                    raise ParseError('On line %i: `%s` '% (j, splitted[1]) +
                            'is not a valid modifier.')
                modifier = splitted[1]
            else:
                modifier = None
            if opcode == 'ORG':
                old_label = None
                origin = evaluate_operand(tokens.pop(0))
            elif opcode == 'END':
                old_label = None # Useless, but we do it anyway
                origin = evaluate_operand(tokens.pop(0))
                break
            elif opcode == 'EQU':
                if label is None and old_label is None:
                    raise ParseError('On line %i: `EQU` used without any '%j +
                            'label.')
                elif label is None:
                    constants[old_label].append('\n' + ' '.join(tokens))
                else:
                    constants[label] = ' '.join(tokens)
                    old_label = label
            else:
                old_label = None
                labels[label] = i

                (A, B) = (None, None)
                if len(tokens) > 0:
                    A = tokens.pop(0).strip(',')
                if len(tokens) > 0:
                    B = tokens.pop(0)
                load_queue.append((opcode, modifier, A, B))
                i += 1

        if raw:
            load = 'ORG %i\n' % origin
        else:
            load = []
        for (i, (opcode, modifier, A, B)) in enumerate(load_queue):
                A = evaluate_operand(A)
                B = evaluate_operand(B)
                inst = core.Instruction(opcode=opcode, modifier=modifier,
                        A=A, B=B)
                if raw:
                    load += str(inst) + '\n'
                else:
                    load.append(inst)
        return (origin, load)

