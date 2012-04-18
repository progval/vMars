#!/usr/bin/env python

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
                if x not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/%':
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
            line = line.upper()
            if SYNTAX.comment_line.match(line):
                continue
            tokens = [x for x in line.split(' ') if x != '']
            if tokens[0].split('.')[0] not in SYNTAX.opcodes:
                label = tokens.pop(0)
                if label.endswith(':'):
                    label = label[0:-1]
            else:
                label = None
            splitted = tokens.pop(0).split('.')
            if splitted[0] not in SYNTAX.opcodes:
                raise ParseError('On line %i: `%s` is not a valid opcode.' %
                        (j, tokens[0]))
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

if __name__ == '__main__':
    import os
    import sys
    import argparse
    parser = argparse.ArgumentParser(
            description='Assembles a RedCode assembly file into a load file.')
    parser.add_argument('--force', '-f', action='store_true',
            help='determines whether existing files will be overwritten')
    parser.add_argument('warriors', metavar='warrior.red', type=file,
            nargs='+', help='file to be assembled')

    for (key, value) in core.MarsProperties().as_dict.items():
        parser.add_argument('--' + key, default=value, type=int)

    try:
        args = vars(parser.parse_args())
    except IOError as e: # Failed to open files
        sys.stderr.write(str(e) + '\n')
        sys.stderr.flush()
        exit()

    assemblies = args.pop('warriors')
    force = args.pop('force')
    properties = core.MarsProperties(**args)
    assembler = Assembler(properties)
    for assembly in assemblies:
        if not assembly.name.endswith('.red'):
            sys.stderr.write('%s does not end with .red.\n' % assembly.name)
            sys.stderr.flush()
            exit()
        dest = assembly.name.replace('.red', '.rc')
        name = os.path.split(dest)[1][0:-len('.rc')]
        print('Assembling %s...' % name)
        try:
            load_file = assembler.assemble(assembly.read(), raw=True)
        except ParseError as e:
            print('\tError: %s' % e.args[0])
            print('\tWarrior %s not assembled.' % name)
            continue
        print('\tWarrior %s successfully assembled.' % name)
        print('\tWriting to %s' % dest)
        if os.path.exists(dest):
            if force:
                print('\tFile %s exists, dropping it.' % dest)
                try:
                    os.unlink(dest)
                except:
                    print('\tError: Could not remove file. Warrior not '
                        'written.')
            else:
                print('\tError: File %s exists, not writing warrior %s.' %
                        (dest, name))
                continue
        try:
            open(dest, 'w').write(load_file[1])
        except Exception as e:
            print('\tError: write failed, file may be corrupted.')
            continue
